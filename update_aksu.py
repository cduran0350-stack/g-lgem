import urllib.request, urllib.parse, json, sys

path = 'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
content = open(path, encoding='utf-8').read().replace('const database = ', '').rstrip(';')
db = json.loads(content)

headers = {'User-Agent': 'GolgemEmlakHarita/1.1 (antigravity@test.com)'}

def get_overpass_geom(name, bbox):
    q = f'[out:json][timeout:60];relation["name"="{name}"]["admin_level"="8"]({bbox});out geom;'
    req = urllib.request.Request('http://overpass-api.de/api/interpreter', 
                                 data=urllib.parse.urlencode({'data': q}).encode('utf-8'),
                                 headers=headers, method='POST')
    try:
        resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    except Exception as e:
        print('Error with overpass for', name, ':', e)
        return None
        
    elements = resp.get('elements', [])
    if not elements:
        return None
        
    for el in elements:
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
                        all_pts.extend(ring)
        if all_pts:
            return {'type': 'Polygon', 'coordinates': [all_pts]}
    return None

aksu = next((d for d in db if d['district'] == 'Aksu'), None)
if aksu:
    alt_entry = next((n for n in aksu['neighborhoods'] if 'alt' in n['name'].lower() or 'ınta' in n['name'].lower()), None)
    if alt_entry:
        geom = get_overpass_geom('Altıntaş Mahallesi', '36.8,30.7,37.0,30.9')
        if geom:
            alt_entry['geom'] = geom
            print('Altıntaş updated!')
            
    erm_entry = next((n for n in aksu['neighborhoods'] if 'ermen' in n['name'].lower()), None)
    if not erm_entry:
        erm_entry = {'name': 'Ermenek', 'color': '#3182CE'}
        aksu['neighborhoods'].append(erm_entry)
        
    geom_e = get_overpass_geom('Ermenek Mahallesi', '36.8,30.6,37.0,30.9')
    if geom_e:
        erm_entry['geom'] = geom_e
        print('Ermenek updated/added!')

with open(path, 'w', encoding='utf-8') as f:
    f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')
print('Done!')
