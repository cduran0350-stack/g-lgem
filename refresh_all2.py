import urllib.request
import urllib.parse
import json
import time

url1 = 'http://overpass-api.de/api/interpreter'
url2 = 'https://lz4.overpass-api.de/api/interpreter'
url3 = 'https://z.overpass-api.de/api/interpreter'
urls = [url1, url2, url3]
url_idx = 0

headers = {'User-Agent': 'GolgemAppBot/1.0 (golgem@test.com)'}

def run_query(q):
    global url_idx
    for attempt in range(5):
        url = urls[url_idx % len(urls)]
        print('Querying', url)
        try:
            req = urllib.request.Request(
                url, 
                data=urllib.parse.urlencode({'data': q}).encode('utf-8'), 
                headers=headers, 
                method='POST'
            )
            # increased timeout on read if overpass is slow
            resp = urllib.request.urlopen(req, timeout=120)
            return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if hasattr(e, 'code') and e.code == 429:
                print('429 Too Many Requests, switching server and waiting 10s...')
                url_idx += 1
                time.sleep(10)
            else:
                print('Error:', e)
                url_idx += 1
                time.sleep(10)
    return {'elements': []}

def get_geom_for_elements(resp_elements):
    nh_list = []
    for el in resp_elements:
        name = el.get('tags', {}).get('name')
        if not name: continue
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
                    if all_pts and all_pts[-1] == ring[0]:
                        all_pts.extend(ring[1:])
                    else:
                        if len(all_pts) > 0 and all_pts[-1] != ring[0] and all_pts[-1] == ring[-1]:
                            all_pts.extend(reversed(ring[:-1]))
                            continue
                        all_pts.extend(ring)
        
        if all_pts:
            if all_pts[0] != all_pts[-1]:
                all_pts.append(all_pts[0])
            geom = {'type': 'Polygon', 'coordinates': [all_pts]}
            color = '#' + str(hex(hash(name) % 0xFFFFFF)[2:].zfill(6))
            nh_list.append({'name': name, 'color': color, 'geom': geom})
    return nh_list

finale_data = []
districts = ['Muratpaşa', 'Kepez', 'Konyaaltı']

for d in districts:
    print(f'Fetching {d}...')
    q = f'[out:json][timeout:90];area["name"="Antalya"]->.a;area["name"="{d}"](area.a)->.d;relation["admin_level"="8"](area.d);out geom;'
    resp = run_query(q)
    nh = get_geom_for_elements(resp.get('elements', []))
    nh.sort(key=lambda x: x['name'])
    finale_data.append({'district': d, 'neighborhoods': nh})
    print(f'Added {len(nh)} for {d}')
    time.sleep(3)

print('Fetching Aksu...')
q = '[out:json][timeout:90];area["name"="Antalya"]->.a;area["name"="Aksu"](area.a)->.d;(relation["name"="Altıntaş Mahallesi"]["admin_level"="8"](area.d);relation["name"="Ermenek Mahallesi"]["admin_level"="8"](area.d););out geom;'
resp = run_query(q)
nh = get_geom_for_elements(resp.get('elements', []))
for n in nh:
    n['name'] = n['name'].replace(' Mahallesi', '').replace(' mahallesi', '')
finale_data.append({'district': 'Aksu', 'neighborhoods': nh})
print(f'Added {len(nh)} for Aksu')

for dist in finale_data:
    for n in dist['neighborhoods']:
        name = n['name']
        name = name.replace(' Mahallesi', '').replace(' mahallesi', '')
        if 'Köyü' not in name and 'Mahallesi' not in name:
            if not name.endswith('Mah.') and not name.endswith('Mah'):
                pass
        n['name'] = name

out_path = 'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('const database = ' + json.dumps(finale_data, ensure_ascii=False) + ';')

print('Saved successfully to mahalle_data.js!')
