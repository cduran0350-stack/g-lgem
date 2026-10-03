import sys, json, urllib.request, urllib.parse, zipfile, io, re
sys.stdout.reconfigure(encoding='utf-8')

path = r'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
raw = open(path, encoding='utf-8').read().replace('const database = ', '').rstrip(';')
db = json.loads(raw)

headers_h = {'User-Agent': 'GolgemApp/1.0'}

# --- Atlasbig'den Altıntaş poligonu (mevcut) ---
aksu = next((d for d in db if d['district'] == 'Aksu'), None)
alt_entry = next((n for n in aksu['neighborhoods'] if 'alt' in n['name'].lower()), None)
existing_geom = alt_entry['geom']  # atlasbig polygon (lat 36.91-36.94)
print("Mevcut Altıntaş (atlasbig):", existing_geom['type'])

# --- Overpass'tan ikinci Altıntaş parçası ---
query = """
[out:json][timeout:30];
relation["name"="Altıntaş Mahallesi"]["admin_level"="8"](36.8,30.79,36.95,30.86);
out geom;
"""
print("Overpass isteği yapılıyor...")
req = urllib.request.Request(
    "http://overpass-api.de/api/interpreter",
    data=urllib.parse.urlencode({'data': query}).encode(),
    headers=headers_h, method='POST'
)
resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
elements = resp.get('elements', [])
print(f"Bulunan ilişki sayısı: {len(elements)}")

overpass_poly = None
for el in elements:
    members = el.get('members', [])
    ways_geom = {}
    for m in members:
        if m.get('type') == 'way' and 'geometry' in m:
            ways_geom[m['ref']] = [[pt['lon'], pt['lat']] for pt in m['geometry']]
    
    # Tüm outer way'leri birleştir
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
        overpass_poly = all_pts
        lats = [c[1] for c in all_pts]
        lngs = [c[0] for c in all_pts]
        print(f"Overpass poligon: {len(all_pts)} nokta, Lat {min(lats):.5f}-{max(lats):.5f}")

# --- Altıntaş'ı sadece Overpass'tan al ---
if overpass_poly:
    alt_entry['geom'] = {"type": "Polygon", "coordinates": [overpass_poly]}
    print("Sadece Overpass verisi kullanıldı.")

# --- Ermenek'i de Overpass'tan al ---
q2 = """
[out:json][timeout:30];
relation["name"="Ermenek Mahallesi"]["admin_level"="8"](36.8,30.6,37.0,30.8);
out geom;
"""
print("Ermenek Overpass isteği...")
req2 = urllib.request.Request(
    "http://overpass-api.de/api/interpreter",
    data=urllib.parse.urlencode({'data': q2}).encode(),
    headers=headers_h, method='POST'
)
resp2 = json.loads(urllib.request.urlopen(req2).read().decode('utf-8'))
for el in resp2.get('elements', []):
    name = el.get('tags', {}).get('name', '')
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
        erm_entry = next((n for n in aksu['neighborhoods'] if 'ermen' in n['name'].lower()), None)
        if erm_entry:
            erm_entry['geom'] = {"type": "Polygon", "coordinates": [all_pts]}
            lats = [c[1] for c in all_pts]
            lngs = [c[0] for c in all_pts]
            print(f"Ermenek guncellendi: {len(all_pts)} nokta, Lat {min(lats):.5f}-{max(lats):.5f}")

# --- Kaydet ---
with open(path, 'w', encoding='utf-8') as f:
    f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')
print("mahalle_data.js guncellendi!")
