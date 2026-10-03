import urllib.request
import json
import urllib.parse

url = "http://overpass-api.de/api/interpreter"
query = """
[out:json][timeout:25];
area["name"="Muratpaşa"]->.mur;
area["name"="Kepez"]->.kep;
area["name"="Konyaaltı"]->.kon;
(
  relation["admin_level"="8"](area.mur);
  relation["admin_level"="8"](area.kep);
  relation["admin_level"="8"](area.kon);
  relation["name"~"Altıntaş Mahallesi|Ermenek Mahallesi"]["admin_level"="8"];
);
out geom;
"""

try:
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as response:
        resp = json.loads(response.read().decode('utf-8'))
        elements = resp.get('elements', [])
        print("Found", len(elements), "neighborhoods.")
        print([e.get('tags', {}).get('name') for e in elements[:10]])
except Exception as e:
    print("Error:", e)
