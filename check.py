import sys, json
sys.stdout.reconfigure(encoding='utf-8')
path = r'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
raw = open(path, encoding='utf-8').read().replace('const database = ', '').rstrip(';')
db = json.loads(raw)
print("Aksu mahalleleri:", [n['name'] for n in db[3]['neighborhoods']])
