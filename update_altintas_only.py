import json, urllib.request, urllib.parse, sys
import osm2geojson

def update_altintas():
    # Read the existing data
    path = r'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read().replace('const database = ', '').rstrip(';')
    db = json.loads(raw)
    
    # Fetch Altintas from overpass perfectly
    query = """
    [out:json][timeout:30];
    relation["name"="Altıntaş Mahallesi"]["admin_level"="8"];
    out geom;
    """
    
    print("Fetching precise Altıntaş from OSM...")
    headers = {'User-Agent': 'GolgemEmlakHarita/1.2'}
    req = urllib.request.Request("http://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({'data': query}).encode('utf-8'), headers=headers, method='POST')
    resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    
    gj = osm2geojson.json2geojson(resp)
    overpass_geom = None
    for feat in gj.get('features', []):
        geom = feat.get('geometry')
        if geom and geom['type'] in ['Polygon', 'MultiPolygon']:
            overpass_geom = geom
            break
            
    if not overpass_geom:
        print("Couldn't fetch Altıntaş polygon.")
        return
        
    print("Fetched Altıntaş successfully!")
    
    # Replace in DB
    found = False
    for dist in db:
        if dist['district'] == 'Aksu':
            for n in dist['neighborhoods']:
                if 'Altıntaş' in n['name']:
                    n['geom'] = overpass_geom
                    found = True
                    print("Updated existing Altıntaş!")
                    
            if not found:
                dist['neighborhoods'].append({
                    "name": "Altıntaş Mah.",
                    "color": "#3182CE",
                    "geom": overpass_geom
                })
                print("Appended Altıntaş as new entry in Aksu!")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')
    print("mahalle_data.js saved perfectly.")

if __name__ == '__main__':
    update_altintas()
