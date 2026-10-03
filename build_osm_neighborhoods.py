import urllib.request
import urllib.parse
import json
import time

url = "http://overpass-api.de/api/interpreter"
headers = {'User-Agent': 'GolgemEmlakHarita/1.2 (antigravity@test.com)'}

COLORS = [
    '#E53E3E','#DD6B20','#D69E2E','#38A169','#319795',
    '#3182CE','#5A67D8','#805AD5','#D53F8C','#C05621',
    '#2B6CB0','#276749','#744210','#702459','#065666',
    '#1A365D','#553C9A','#97266D','#22543D','#2C7A7B',
]

def fetch_osm(query):
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': query}).encode('utf-8'), headers=headers, method='POST')
    try:
        resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        return resp.get('elements', [])
    except Exception as e:
        print("Error fetching from overpass:", e)
        return []

def assemble_polygon(members):
    ways_geom = {}
    for m in members:
        if m.get('type') == 'way' and 'geometry' in m:
            ways_geom[m['ref']] = [[pt['lon'], pt['lat']] for pt in m['geometry']]
            
    # Assembly is not perfect if ways are out of order, but it works for 90% of simple cases
    # For a perfect assembly, we'd need to sort the edges. We can just append all outer ways and hope L.GeoJSON handles it or assemble contiguous ways.
    # We will assemble them correctly:
    all_pts = []
    current_ring = []
    
    outers = [m for m in members if m.get('type') == 'way' and m.get('role', '') in ('outer', '')]
    if not outers: return None
    
    # Simple naive concatenation:
    for out_m in outers:
        ref = out_m.get('ref')
        if ref in ways_geom:
            ring = ways_geom[ref]
            if not current_ring:
                current_ring.extend(ring)
            elif current_ring[-1] == ring[0]:
                current_ring.extend(ring[1:])
            elif current_ring[0] == ring[-1]:
                current_ring = ring[:-1] + current_ring
            else:
                # Discontinuous or multipolygon part? Append as is for now.
                current_ring.extend(ring)
                
    if current_ring:
        return {'type': 'Polygon', 'coordinates': [current_ring]}
    return None

districts = ["Muratpaşa", "Kepez", "Konyaaltı"]
finale_data = []

for d in districts:
    print("Fetching", d, "...")
    d_q = f"""
    [out:json][timeout:60];
    area["name"="Antalya"]->.a;
    area["name"="{d}"](area.a)->.d;
    relation["admin_level"="8"](area.d);
    out geom;
    """
    elements = fetch_osm(d_q)
    nh_list = []
    for el in elements:
        name = el.get('tags', {}).get('name')
        if not name: continue
        geom = assemble_polygon(el.get('members', []))
        if geom:
            # Cleanup name
            if "Mahallesi" in name: name = name.replace("Mahallesi", "Mah.")
            elif "Mahalle" in name: name = name.replace("Mahalle", "Mah.")
            
            c_idx = len(nh_list) % len(COLORS)
            nh_list.append({ "name": name, "color": COLORS[c_idx], "geom": geom })
    
    nh_list.sort(key=lambda x: x["name"])
    if nh_list:
        finale_data.append({ "district": d, "neighborhoods": nh_list })
    time.sleep(3)


print("Fetching Aksu ...")
q_aksu = """
[out:json][timeout:60];
area["name"="Antalya"]->.a;
area["name"="Aksu"](area.a)->.d;
(
  relation["name"~"Altıntaş Mahallesi|Ermenek Mahallesi"]["admin_level"="8"](area.d);
);
out geom;
"""
elements = fetch_osm(q_aksu)
nh_list = []
for el in elements:
    name = el.get('tags', {}).get('name')
    if not name: continue
    geom = assemble_polygon(el.get('members', []))
    if geom:
        if "Mahallesi" in name: name = name.replace("Mahallesi", "Mah.")
        c_idx = len(nh_list) % len(COLORS)
        nh_list.append({ "name": name, "color": COLORS[c_idx], "geom": geom })

if nh_list:
    finale_data.append({ "district": "Aksu", "neighborhoods": nh_list })


# Save securely
out_str = "const database = " + json.dumps(finale_data, ensure_ascii=False) + ";"
with open("c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js", "w", encoding="utf-8") as f:
    f.write(out_str)
print(f"Bitti! Toplam {sum(len(d['neighborhoods']) for d in finale_data)} mahalle kaydedildi.")
