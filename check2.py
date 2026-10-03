import sys, json
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request, re, zipfile, io

headers = {'User-Agent': 'Mozilla/5.0'}
html = urllib.request.urlopen(urllib.request.Request('https://www.atlasbig.com/tr/antalya-aksunun-mahalleleri', headers=headers)).read().decode('utf-8')
m = re.search(r'(https://farm\.atlasbig\.com/.*?package\.json\.zip)', html)
zdata = urllib.request.urlopen(urllib.request.Request(m.group(1), headers=headers)).read()
pkg = json.loads(zipfile.ZipFile(io.BytesIO(zdata)).open('data').read().decode('utf-8'))
names_primary = pkg.get('names', {}).get('primary', [])
print("Tüm Aksu mahalle isimleri:")
for i, entry in enumerate(names_primary):
    if isinstance(entry, dict):
        name = entry.get('default', '')
    elif isinstance(entry, list) and entry:
        name = entry[0].get('default', '') if isinstance(entry[0], dict) else str(entry[0])
    else:
        name = str(entry)
    print(f"  {i}: {name}")
