import sys, json, urllib.request, urllib.parse, time
sys.stdout.reconfigure(encoding='utf-8')

path = 'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
db = json.loads(open(path, encoding='utf-8').read().replace('const database = ', '').rstrip(';'))

OVERPASS_URLS = [
    'https://overpass-api.de/api/interpreter',
    'https://lz4.overpass-api.de/api/interpreter',
    'https://z.overpass-api.de/api/interpreter',
]
url_idx = 0
headers = {'User-Agent': 'GolgemAppBot/1.0 (golgem@test.com)'}

def run_query(q):
    global url_idx
    for attempt in range(6):
        url = OVERPASS_URLS[url_idx % len(OVERPASS_URLS)]
        try:
            req = urllib.request.Request(url, 
                data=urllib.parse.urlencode({'data': q}).encode('utf-8'),
                headers=headers, method='POST')
            resp = urllib.request.urlopen(req, timeout=90)
            return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f'  Attempt {attempt+1} failed ({url}): {e}')
            url_idx += 1
            time.sleep(8)
    return {'elements': []}

def extract_polygon(el):
    """
    OSM relation'dan Polygon GeoJSON çıkar.
    Outer way'leri birleştirir.
    """
    members = el.get('members', [])
    ways_geom = {}
    for m in members:
        if m.get('type') == 'way' and 'geometry' in m:
            ways_geom[m['ref']] = [[pt['lon'], pt['lat']] for pt in m['geometry']]
    
    # Outer ring'leri topla
    outer_ways = [m for m in members
                  if m.get('type') == 'way' and m.get('role', '') in ('outer', '')]
    
    all_pts = []
    for m in outer_ways:
        ref = m.get('ref')
        if ref not in ways_geom:
            continue
        ring = ways_geom[ref]
        if not all_pts:
            all_pts.extend(ring)
        elif all_pts[-1] == ring[0]:
            all_pts.extend(ring[1:])
        elif all_pts[-1] == ring[-1]:
            all_pts.extend(reversed(ring[:-1]))
        else:
            all_pts.extend(ring)
    
    if len(all_pts) < 3:
        return None
    if all_pts[0] != all_pts[-1]:
        all_pts.append(all_pts[0])
    return {'type': 'Polygon', 'coordinates': [all_pts]}

# ─── İlçe adlarını OSM'deki karşılıklarıyla eşleştir ───
district_osm = {
    'Muratpaşa': 'Muratpaşa',
    'Kepez': 'Kepez',
    'Konyaaltı': 'Konyaaltı',
    'Aksu': 'Aksu',
}

update_count = 0
fail_count = 0

for dist in db:
    d_name = dist['district']
    osm_d = district_osm.get(d_name, d_name)
    
    nh_names = [n['name'] for n in dist['neighborhoods']]
    print(f"\n=== {d_name} ({len(nh_names)} mahalle) ===")

    # OSM adları için mahalleyi "X Mahallesi" formatında sorgula
    # Toplu sorgu: tüm mahalleleri tek seferde çek
    q = f'''
[out:json][timeout:90];
area["name"="Antalya"]->.a;
area["name"="{osm_d}"](area.a)->.d;
relation["admin_level"="8"](area.d);
out geom;
'''
    print(f"  Overpass'tan {d_name} sınırları çekiliyor...")
    resp = run_query(q)
    elements = resp.get('elements', [])
    print(f"  {len(elements)} sonuç geldi.")
    
    # OSM sonuçlarını isimle indeksle
    osm_by_name = {}
    for el in elements:
        nm = el.get('tags', {}).get('name', '')
        if nm:
            osm_by_name[nm] = el
            # "X Mahallesi" → "X Mah." şeklinde de ekle
            short = nm.replace(' Mahallesi', ' Mah.').replace(' mahallesi', ' Mah.')
            osm_by_name[short] = el
    
    # Her mahalleyi eşleştir
    for nh in dist['neighborhoods']:
        nh_name = nh['name']
        
        # Tam eşleşme
        el = osm_by_name.get(nh_name)
        
        # Kısmi eşleşme: "Güzeloba Mah." → "Güzeloba Mahallesi"
        if not el:
            long_name = nh_name.replace(' Mah.', ' Mahallesi')
            el = osm_by_name.get(long_name)
        
        if el:
            geom = extract_polygon(el)
            if geom:
                nh['geom'] = geom
                update_count += 1
                print(f"  ✓ {nh_name}")
            else:
                print(f"  ! Polygon çıkarılamadı: {nh_name}")
                fail_count += 1
        else:
            print(f"  ? Eşleşme bulunamadı: {nh_name}")
            fail_count += 1
    
    time.sleep(3)  # rate limit

# Kaydet
with open(path, 'w', encoding='utf-8') as f:
    f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')

print(f"\n=== TAMAMLANDI ===")
print(f"  Güncellenen: {update_count}")
print(f"  Güncellenemeyen: {fail_count}")
print(f"  mahalle_data.js kaydedildi!")
