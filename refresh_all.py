import urllib.request
import urllib.parse
import json
import time

url = "http://overpass-api.de/api/interpreter"
headers = {'User-Agent': 'GolgemEmlakHarita/1.1 (antigravity)'}

def get_geom_for_elements(resp_elements):
    nh_list = []
    for el in resp_elements:
        name = el.get('tags', {}).get('name')
        if not name: 
            continue
            
        members = el.get('members', [])
        ways_geom = {}
        for m in members:
            if m.get('type') == 'way' and 'geometry' in m:
                ways_geom[m['ref']] = [[pt['lon'], pt['lat']] for pt in m['geometry']]
        
        all_pts = []
        for m in members:
            if m.get('type') == 'way' and m.get('role', '') in ('outer', ''):
                ref = m.get('ref')
                if ref in ways_geom:
                    ring = ways_geom[ref]
                    if all_pts and all_pts[-1] == ring[0]: # Join contiguous ways
                        all_pts.extend(ring[1:])
                    else:
                        if len(all_pts) > 0 and all_pts[-1] != ring[0]:
                            # Sometimes OSM ways are backwards
                            if all_pts[-1] == ring[-1]:
                                all_pts.extend(reversed(ring[:-1]))
                                continue
                        all_pts.extend(ring)
        
        if all_pts:
            if all_pts[0] != all_pts[-1]:
                all_pts.append(all_pts[0]) # ensure closed ring
            # We must wrap it in coordinates double array for GeoJSON Polygon
            geom = {'type': 'Polygon', 'coordinates': [all_pts]}
            color = "#" + str(hex(hash(name) % 0xFFFFFF)[2:].zfill(6))
            nh_list.append({"name": name, "color": color, "geom": geom})
    return nh_list

finale_data = []

districts = ["Muratpaşa", "Kepez", "Konyaaltı"]

for d in districts:
    print(f"Fetching {d}...")
    d_q = f"""
    [out:json][timeout:60];
    area["name"="Antalya"]->.a;
    area["name"="{d}"](area.a)->.d;
    relation["admin_level"="8"](area.d);
    out geom;
    """
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': d_q}).encode('utf-8'), headers=headers, method='POST')
        resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        nh_list = get_geom_for_elements(resp.get('elements', []))
        if nh_list:
            nh_list.sort(key=lambda x: x['name'])
            finale_data.append({ "district": d, "neighborhoods": nh_list })
            print(f"Safely added {len(nh_list)} neighborhoods for {d}.")
    except Exception as e:
        print("Error fetching", d, e)
    
    time.sleep(3)

print("Fetching Aksu (Only Altıntaş and Ermenek)...")
q_aksu = """
[out:json][timeout:60];
area["name"="Antalya"]->.a;
area["name"="Aksu"](area.a)->.d;
(
  relation["name"="Altıntaş Mahallesi"]["admin_level"="8"](area.d);
  relation["name"="Ermenek Mahallesi"]["admin_level"="8"](area.d);
);
out geom;
"""
try:
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': q_aksu}).encode('utf-8'), headers=headers, method='POST')
    resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    nh_list = get_geom_for_elements(resp.get('elements', []))
    for nh in nh_list:
        nh['name'] = nh['name'].replace(' Mahallesi', '') # Clean name
    if nh_list:
        finale_data.append({ "district": "Aksu", "neighborhoods": nh_list })
        print(f"Safely added {len(nh_list)} neighborhoods for Aksu.")
except Exception as e:
    print("Error fetching Aksu", e)

# Clean up names for all districts
for dist in finale_data:
    for nh in dist['neighborhoods']:
        name = nh['name']
        name = name.replace(' Mahallesi', '').replace(' mahallesi', '')
        # Many keep "Mah." in the name, others don't in OSM.
        # But we standardize them to NOT have "Mahallesi" but maybe add it later, actually index.html expects the pure name.
        if "Köyü" not in name and "Mahallesi" not in name:
            if not name.endswith("Mah.") and not name.endswith("Mah"):
                # some names in OSM are already with "Mah." or purely the name. 
                pass
        
        nh['name'] = name

out_path = 'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
with open(out_path, "w", encoding="utf-8") as f:
    f.write("const database = " + json.dumps(finale_data, ensure_ascii=False) + ";")

print("Saved accurately from Overpass to mahalle_data.js!")
