import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, urllib.request, urllib.parse
import osm2geojson

path = r'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'

# Antalya Aksu bbox: yaklaşık 36.80-36.95 kuzey, 30.70-30.95 doğu
# Bu bbox ile sadece Antalya Aksu'daki Altıntaş gelecek
query = """
[out:json][timeout:60];
relation["name"="Altıntaş Mahallesi"]["admin_level"="8"](36.75,30.55,37.05,31.10);
out geom;
"""

headers = {'User-Agent': 'GolgemEmlakHarita/1.2'}
print("Antalya Aksu bbox ile Altıntaş çekiliyor...")

urls = [
    'http://overpass-api.de/api/interpreter',
    'https://lz4.overpass-api.de/api/interpreter',
    'https://z.overpass-api.de/api/interpreter'
]
import time
geom = None
for url in urls:
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': query}).encode('utf-8'), headers=headers, method='POST')
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))
        print(f"Gelen eleman sayısı: {len(resp.get('elements', []))}")
        
        for el in resp.get('elements', []):
            tag_name = el.get('tags', {}).get('name', '')
            tag_admin = el.get('tags', {}).get('admin_level', '')
            print(f"  Bulunan: {tag_name} (admin_level={tag_admin})")
        
        gj = osm2geojson.json2geojson(resp)
        for feat in gj.get('features', []):
            g = feat.get('geometry')
            if g and g['type'] in ['Polygon', 'MultiPolygon']:
                pts = g['coordinates'][0][0] if g['type'] == 'MultiPolygon' else g['coordinates'][0]
                lats = [p[1] for p in pts]
                lngs = [p[0] for p in pts]
                print(f"Tip: {g['type']}, Nokta: {len(pts)}")
                print(f"Lat: {min(lats):.5f} - {max(lats):.5f}")
                print(f"Lng: {min(lngs):.5f} - {max(lngs):.5f}")
                geom = g
                break
        if geom:
            break
    except Exception as e:
        print(f"Hata ({url}): {e}")
        time.sleep(5)

if geom:
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read().replace('const database = ', '').rstrip(';')
    db = json.loads(raw)
    
    for dist in db:
        if dist['district'] == 'Aksu':
            for n in dist['neighborhoods']:
                if 'Altıntaş' in n['name']:
                    n['geom'] = geom
                    n['color'] = '#3182CE'
                    print(f"Güncellendi: {n['name']}")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')
    print("Kaydedildi!")
else:
    print("OSM'de Antalya Aksu'da Altıntaş Mahallesi bulunamadı!")
    print("Elle poligon ataması yapılacak...")
