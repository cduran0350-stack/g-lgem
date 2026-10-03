import sys, urllib.request, urllib.parse, re, json, zipfile, io
sys.stdout.reconfigure(encoding='utf-8')

cities = [
    ('Muratpaşa', 'https://www.atlasbig.com/tr/antalya-muratpasanin-mahalleleri'),
    ('Kepez', 'https://www.atlasbig.com/tr/antalya-kepezin-mahalleleri'),
    ('Konyaaltı', 'https://www.atlasbig.com/tr/antalya-konyaaltinin-mahalleleri'),
    ('Aksu', 'https://www.atlasbig.com/tr/antalya-aksunun-mahalleleri')
]

AKSU_ALLOWED = ['altıntaş', 'ermenek']

headers = {'User-Agent': 'Mozilla/5.0'}

COLORS = [
    '#E53E3E','#DD6B20','#D69E2E','#38A169','#319795',
    '#3182CE','#5A67D8','#805AD5','#D53F8C','#C05621',
    '#2B6CB0','#276749','#744210','#702459','#065666',
    '#1A365D','#553C9A','#97266D','#22543D','#2C7A7B',
    '#285E61','#44337A','#521B41','#1D4044','#2A4365',
    '#E53E3E','#DD6B20','#D69E2E','#38A169','#319795'
]

db = []

def cleanup_name(name):
    name = str(name).strip()
    name = name.replace(' Mahallesi', ' Mah.').replace(' mahallesi', ' Mah.')
    if 'Mah.' not in name and 'Köy' not in name:
        name = name + ' Mah.'
    return name

for c_name, c_url in cities:
    print(f"Processing {c_name}...")
    try:
        req = urllib.request.Request(c_url, headers=headers)
        html = urllib.request.urlopen(req).read().decode('utf-8')
        m = re.search(r'(https://farm\.atlasbig\.com/.*?package\.json\.zip)', html)
        if not m:
            print(f"  Zip not found for {c_name}")
            continue
        
        zdata = urllib.request.urlopen(urllib.request.Request(m.group(1), headers=headers)).read()
        raw = zipfile.ZipFile(io.BytesIO(zdata)).open('data').read()
        pkg = json.loads(raw.decode('utf-8'))
        
        areas = pkg.get('areas', {})
        features = areas.get('features', [])
        names_primary = pkg.get('names', {}).get('primary', [])
        
        nh_list = []
        color_idx = 0
        
        for i, feat in enumerate(features):
            name = ''
            if i < len(names_primary):
                entry = names_primary[i]
                if isinstance(entry, dict):
                    # CRITICAL: use get with fallback order, preserving real unicode
                    name = entry.get('tr') or entry.get('default') or list(entry.values())[0]
                elif isinstance(entry, str):
                    name = entry
                elif isinstance(entry, list) and entry:
                    first = entry[0]
                    name = first.get('default', '') if isinstance(first, dict) else str(first)
            
            if not name:
                props = feat.get('properties') or {}
                name = props.get('name') or props.get('isim') or ''
            
            if not name:
                continue
            
            name = cleanup_name(name)
            
            # Aksu filter
            if c_name == 'Aksu':
                if not any(a in name.lower() for a in AKSU_ALLOWED):
                    continue
            
            geom = feat.get('geometry', {})
            if geom.get('type') not in ('Polygon', 'MultiPolygon'):
                continue
            
            nh_list.append({
                'name': name,
                'geom': geom,
                'color': COLORS[color_idx % len(COLORS)]
            })
            color_idx += 1
            print(f"  + {name}")
        
        if nh_list:
            nh_list.sort(key=lambda x: x['name'])
            for i, nh in enumerate(nh_list):
                nh['color'] = COLORS[i % len(COLORS)]
            db.append({'district': c_name, 'neighborhoods': nh_list})
            print(f"  Total: {len(nh_list)} mahalle kaydedildi")
        else:
            print(f"  UYARI: {c_name} icin mahalle bulunamadi!")
            
    except Exception as e:
        import traceback
        print(f"  HATA {c_name}: {e}")
        traceback.print_exc()

out_path = 'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')

print(f"\nTamamlandi! Toplam ilce: {len(db)}")
for d in db:
    print(f"  {d['district']}: {len(d['neighborhoods'])} mahalle")
