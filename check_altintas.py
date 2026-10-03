import sys, json
sys.stdout.reconfigure(encoding='utf-8')

path = r'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
raw = open(path, encoding='utf-8').read().replace('const database = ', '').rstrip(';')
db = json.loads(raw)

aksu = next((d for d in db if d['district'] == 'Aksu'), None)
altintas = next((n for n in aksu['neighborhoods'] if 'alt' in n['name'].lower()), None)

geom = altintas['geom']
print("Geometry type:", geom['type'])

# coords bağlamında min/max lat/lng bul
if geom['type'] == 'Polygon':
    coords = geom['coordinates'][0]
    lats = [c[1] for c in coords]
    lngs = [c[0] for c in coords]
    print(f"Lat: {min(lats):.5f} - {max(lats):.5f}")
    print(f"Lng: {min(lngs):.5f} - {max(lngs):.5f}")
    print("Nokta sayısı:", len(coords))
elif geom['type'] == 'MultiPolygon':
    for i, poly in enumerate(geom['coordinates']):
        coords = poly[0]
        lats = [c[1] for c in coords]
        lngs = [c[0] for c in coords]
        print(f"Polygon {i}: Lat {min(lats):.5f}-{max(lats):.5f}, Lng {min(lngs):.5f}-{max(lngs):.5f}, {len(coords)} nokta")
