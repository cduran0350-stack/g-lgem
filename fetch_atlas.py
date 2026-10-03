import urllib.request
import json, traceback

cities = [
    ('Muratpaşa', 'https://www.atlasbig.com/tr/antalya-muratpasanin-mahalleleri'),
    ('Kepez', 'https://www.atlasbig.com/tr/antalya-kepezin-mahalleleri'),
    ('Konyaaltı', 'https://www.atlasbig.com/tr/antalya-konyaaltinin-mahalleleri'),
    ('Aksu', 'https://www.atlasbig.com/tr/antalya-aksunun-mahalleleri')
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
db = []

for c_name, c_url in cities:
    req = urllib.request.Request(c_url, headers=headers)
    try:
        print(f"Fetching {c_name}...")
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        idx_start = html.find('{"type":"FeatureCollection"')
        if idx_start == -1:
            idx_start = html.find('{"type": "FeatureCollection"')
            
        if idx_start != -1:
            brace_count = 0
            idx_end = -1
            in_str = False
            escape = False
            
            for i in range(idx_start, len(html)):
                char = html[i]
                if escape:
                    escape = False
                    continue
                if char == '"':
                    in_str = not in_str
                elif char == '\\':
                    escape = True
                elif char == '{' and not in_str:
                    brace_count += 1
                elif char == '}' and not in_str:
                    brace_count -= 1
                    if brace_count == 0:
                        idx_end = i
                        break
                        
            if idx_end != -1:
                json_str = html[idx_start:idx_end+1]
                geojson = json.loads(json_str)
                nh_list = []
                for f in geojson.get('features', []):
                    prop = f.get('properties', {})
                    name = prop.get('name') or prop.get('Name') or prop.get('NAME') or prop.get('isim')
                    if not name:
                        for k,v in prop.items():
                            if isinstance(v, str) and ('Mahalle' in v or 'mahalle' in v or 'Köyü' in v): name = v
                            elif isinstance(v, str) and not name: name = v
                    
                    if name:
                        name = name.strip()
                        if "Mah" not in name and "Köy" not in name:
                            name = name.title() + " Mah."
                        else:
                            name = name.title()
                    else: 
                        name = 'Bilinmeyen Mah.'
                        
                    if c_name == 'Aksu':
                        nm = name.lower()
                        if "altıntaş" not in nm and "altintas" not in nm and "ermen" not in nm:
                            continue
                            
                    geom = f.get('geometry', {})
                    if geom.get('type') in ('Polygon', 'MultiPolygon'):
                        # Using 3-byte valid hex for leaflet polygon
                        h = str(hex(hash(name) % 0xFFFFFF)[2:].zfill(6))
                        nh_list.append({
                            'name': name,
                            'geom': geom,
                            'color': f'#{h}'
                        })
                if nh_list:
                    # Sort neighborhood names alphabetically
                    nh_list.sort(key=lambda x: x['name'])
                    db.append({ 'district': c_name, 'neighborhoods': nh_list })
                    print(f'Success: {c_name} extracted {len(nh_list)} neighborhoods.')
            else:
                print(f'Error {c_name}: Brace tracking failed.')
        else:
            print(f'Error {c_name}: FeatureCollection not found.')
            
    except Exception as e:
        print(f'Error fetching {c_name}: {e}')

with open('c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js', 'w', encoding='utf-8') as f:
    f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')
print('Script finished successfully!')
