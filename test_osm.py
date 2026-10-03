import urllib.request
import urllib.parse
import json
import osm2geojson
import sys

url = "http://overpass-api.de/api/interpreter"
headers = {'User-Agent': 'TestBot/1.2'}

q = """
[out:json][timeout:25];
relation["name"="Ermenek Mahallesi"]["admin_level"="8"];
out geom;
"""

try:
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': q}).encode('utf-8'), headers=headers, method='POST')
    resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    
    geojson = osm2geojson.json2geojson(resp)
    for feat in geojson['features']:
        print(feat['properties'].get('tags', {}).get('name'), feat['geometry']['type'], feat['geometry']['coordinates'][0][0])
except Exception as e:
    print(e)
