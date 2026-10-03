import urllib.request
import urllib.parse
import json
import os
import time

url = "http://overpass-api.de/api/interpreter"

# One single query to prevent rate limiting
q = """
[out:json][timeout:60];
area["name"="Antalya"]->.a;
area["name"="Muratpaşa"](area.a)->.mur;
area["name"="Kepez"](area.a)->.kep;
area["name"="Konyaaltı"](area.a)->.kon;
area["name"="Aksu"](area.a)->.aks;

(
  relation["admin_level"="8"](area.mur);
  relation["admin_level"="8"](area.kep);
  relation["admin_level"="8"](area.kon);
  relation["name"~"Altıntaş Mahallesi|Ermenek Mahallesi"]["admin_level"="8"](area.aks);
);
out geom;
"""

headers = {
    'User-Agent': 'GolgemEmlakHarita/1.1 (antigravity@test.com)'
}

try:
    print("Fetching single robust query from Overpass...")
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': q}).encode('utf-8'), headers=headers, method='POST')
    resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    
    districts_map = {
        "Muratpaşa": [],
        "Kepez": [],
        "Konyaaltı": [],
        "Aksu": []
    }
    
    for el in resp.get('elements', []):
        name = el.get('tags', {}).get('name')
        if not name: continue
        
        # OSM doesn't return district directly on admin_level=8 easily.
        # But we can approximate by the tags or just group them by checking is_in 
        # or we can do 4 queries slowly. We will just keep 4 queries but sleep.
except Exception as e:
    print("Error:", e)

# Doing 4 separate queries slowly
districts = ["Muratpaşa", "Kepez", "Konyaaltı"]
finale_data = []

for d in districts:
    print("Fetching", d, "...")
    d_q = f"""
    [out:json][timeout:25];
    area["name"="Antalya"]->.a;
    area["name"="{d}"](area.a)->.d;
    relation["admin_level"="8"](area.d);
    out geom;
    """
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': d_q}).encode('utf-8'), headers=headers, method='POST')
        resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        
        nh_list = []
        for el in resp.get('elements', []):
            name = el.get('tags', {}).get('name')
            if not name: continue
            
            lines = []
            for m in el.get('members', []):
                if m.get('type') == 'way' and 'geometry' in m:
                    lines.append([[pt['lat'], pt['lon']] for pt in m['geometry']])
            
            if lines:
                nh_list.append({ "name": name, "color": "#" + str(hex(hash(name) % 0xFFFFFF)[2:].zfill(6)), "lines": lines })
        
        finale_data.append({ "district": d, "neighborhoods": nh_list })
        
    except Exception as e:
        print("Error fetching", d, e)
    
    time.sleep(4) # Respect rate limits

print("Fetching Aksu ...")
try:
    q_aksu = """
    [out:json][timeout:25];
    area["name"="Antalya"]->.a;
    area["name"="Aksu"](area.a)->.d;
    (
      relation["name"="Altıntaş Mahallesi"]["admin_level"="8"](area.d);
      relation["name"="Ermenek Mahallesi"]["admin_level"="8"](area.d);
    );
    out geom;
    """
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': q_aksu}).encode('utf-8'), headers=headers, method='POST')
    resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    nh_list = []
    for el in resp.get('elements', []):
        name = el.get('tags', {}).get('name')
        if not name: continue
        lines = []
        for m in el.get('members', []):
            if m.get('type') == 'way' and 'geometry' in m:
                lines.append([[pt['lat'], pt['lon']] for pt in m['geometry']])
        if lines:
            nh_list.append({ "name": name, "color": "#" + str(hex(hash(name) % 0xFFFFFF)[2:].zfill(6)), "lines": lines })
    if nh_list:
        finale_data.append({ "district": "Aksu", "neighborhoods": nh_list })
except Exception as e:
    print("Error fetching Aksu", e)

with open("c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js", "w", encoding="utf-8") as f:
    f.write("const database = " + json.dumps(finale_data, ensure_ascii=False) + ";")

print("Saved to mahalle_data.js!")
