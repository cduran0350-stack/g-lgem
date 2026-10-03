import json
import urllib.request
import urllib.parse
import re

print('Fetching correct names from Overpass...')
correct_names = []
districts = ["Muratpaşa", "Kepez", "Konyaaltı", "Aksu"]
headers = {'User-Agent': 'GolgemAppBot/1.0 (golgem@test.com)'}
for d in districts:
    q = f'[out:json][timeout:25];area["name"="Antalya"]->.a;area["name"="{d}"](area.a)->.d;relation["admin_level"="8"](area.d);out tags;'
    req = urllib.request.Request("http://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({'data': q}).encode('utf-8'), headers=headers)
    resp = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    for el in resp.get('elements', []):
        name = el.get('tags', {}).get('name')
        if name:
            correct_names.append(name.replace(' Mahallesi', ' Mah.').replace(' mahallesi', ' Mah.'))

# Add missing aliases if any
correct_names.extend(["Altıntaş Mah.", "Ermenek Mah.", "Çaybaşı Mah.", "Şirinyalı Mah.", "Çağlayan Mah.", "Meydankavağı Mah."])

# Normalization for matching
import unicodedata
def normalize_for_match(s):
    s = s.replace('\ufffd', '')
    s = s.replace('', '')
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s.lower().replace(' ', '')

print('Loading database...')
path = 'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
content = open(path, encoding='utf-8').read().replace('const database = ', '').rstrip(';')
db = json.loads(content)

for d in db:
    for n in d['neighborhoods']:
        broken = n['name']
        if '\ufffd' in broken or '' in broken:
            # find best match
            broken_norm = normalize_for_match(broken)
            best_match = None
            for cn in correct_names:
                cn_norm = normalize_for_match(cn)
                if broken_norm in cn_norm or cn_norm in broken_norm:
                    best_match = cn
                    break
            
            # If standard fuzzy fails, try finding by matching character structure
            if not best_match:
                for cn in correct_names:
                    if len(broken) == len(cn):
                        match_count = sum(1 for a, b in zip(broken, cn) if a == b or a in ('\ufffd', ''))
                        if match_count >= len(broken) - 4:
                            best_match = cn
                            break
                            
            if best_match:
                n['name'] = best_match
            else:
                print(f"COULD NOT MATCH: {broken}")

# Final explicit fixes for known ones just in case
for d in db:
    for n in d['neighborhoods']:
        if 'Alt' in n['name'] and 'nta' in n['name']: n['name'] = 'Altıntaş Mah.'
        if 'Ermen' in n['name']: n['name'] = 'Ermenek Mah.'

with open(path, 'w', encoding='utf-8') as f:
    f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')

print('Names fixed successfully!')
