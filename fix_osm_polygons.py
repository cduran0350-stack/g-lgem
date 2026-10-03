import urllib.request
import urllib.parse
import json
import time
import osm2geojson

urls = [
    'http://overpass-api.de/api/interpreter',
    'https://lz4.overpass-api.de/api/interpreter',
    'https://z.overpass-api.de/api/interpreter'
]
url_idx = 0

headers = {'User-Agent': 'GolgemEmlakHarita/1.2'}

COLORS = [
    '#E53E3E','#DD6B20','#D69E2E','#38A169','#319795',
    '#3182CE','#5A67D8','#805AD5','#D53F8C','#C05621',
    '#2B6CB0','#276749','#744210','#702459','#065666',
    '#1A365D','#553C9A','#97266D','#22543D','#2C7A7B',
]

def fetch_osm_geojson(query):
    global url_idx
    for attempt in range(5):
        url = urls[url_idx % len(urls)]
        req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': query}).encode('utf-8'), headers=headers, method='POST')
        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=120).read().decode('utf-8'))
            return osm2geojson.json2geojson(resp)
        except Exception as e:
            if hasattr(e, 'code') and e.code == 429:
                print(f"429 Too Many Requests on {url}, switching server...")
            else:
                print(f"Error fetching from overpass ({url}): {e}")
            url_idx += 1
            time.sleep(10)
    return None

districts = ["Muratpaşa", "Kepez", "Konyaaltı"]
finale_data = []

for d in districts:
    print(f"Fetching {d} ...")
    d_q = f"""
    [out:json][timeout:90];
    area["name"="Antalya"]->.a;
    area["name"="{d}"](area.a)->.d;
    relation["admin_level"="8"](area.d);
    out geom;
    """
    gj = fetch_osm_geojson(d_q)
    if not gj:
        continue
    
    # Process features
    nh_list = []
    
    for feat in gj.get('features', []):
        props = feat.get('properties', {})
        tags = props.get('tags', {})
        name = tags.get('name')
        if not name:
            continue
            
        geom = feat.get('geometry')
        if not geom:
            continue
            
        if "Mahallesi" in name: 
            name = name.replace("Mahallesi", "Mah.")
        elif "Mahalle" in name: 
            name = name.replace("Mahalle", "Mah.")
            
        # some polygons might just be multilinestrings if relation is broken, but osm2geojson tries its best
        if geom['type'] not in ['Polygon', 'MultiPolygon']:
            # Overpass relation to polygon might fallback to LineString if poorly formed. In Antalya they are usually fine.
            continue
            
        c_idx = len(nh_list) % len(COLORS)
        nh_list.append({ "name": name, "color": COLORS[c_idx], "geom": geom })
        
    nh_list.sort(key=lambda x: x["name"])
    if nh_list:
        finale_data.append({ "district": d, "neighborhoods": nh_list })
    time.sleep(3)

print("Fetching Aksu ...")
q_aksu = """
[out:json][timeout:90];
(
  relation["name"="Altıntaş Mahallesi"]["admin_level"="8"];
  relation["name"="Ermenek Mahallesi"]["admin_level"="8"];
);
out geom;
"""
gj = fetch_osm_geojson(q_aksu)
if gj:
    nh_list = []
    for feat in gj.get('features', []):
        tags = feat.get('properties', {}).get('tags', {})
        name = tags.get('name')
        if not name: continue
        geom = feat.get('geometry')
        if geom and geom['type'] in ['Polygon', 'MultiPolygon']:
            if "Mahallesi" in name: name = name.replace("Mahallesi", " Mah.")
            elif "Mahalle" in name: name = name.replace("Mahalle", " Mah.")
            c_idx = len(nh_list) % len(COLORS)
            nh_list.append({ "name": name, "color": COLORS[c_idx], "geom": geom })
            
    nh_list.sort(key=lambda x: x["name"])
    if nh_list:
        finale_data.append({ "district": "Aksu", "neighborhoods": nh_list })


out_str = "const database = " + json.dumps(finale_data, ensure_ascii=False) + ";"
with open("c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js", "w", encoding="utf-8") as f:
    f.write(out_str)

print(f"Bitti! Toplam {sum(len(d['neighborhoods']) for d in finale_data)} mahalle kaydedildi.")
