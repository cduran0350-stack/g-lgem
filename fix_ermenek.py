import sys, json
sys.stdout.reconfigure(encoding='utf-8')

path = r'c:/Users/Ayşe Nur/Desktop/gölgem/mahalle_data.js'
raw = open(path, encoding='utf-8').read().replace('const database = ', '').rstrip(';')
db = json.loads(raw)

# Muratpaşa'dan Ermenek'i bul ve ayrı "Aksu" altına kopyala (zaten Muratpaşa'nın mahalleleri listesinde)
muratpasa = next((d for d in db if d['district'] == 'Muratpaşa'), None)
aksu = next((d for d in db if d['district'] == 'Aksu'), None)

if muratpasa and aksu:
    ermenek = next((n for n in muratpasa['neighborhoods'] if 'ermenek' in n['name'].lower()), None)
    if ermenek:
        # Ermenek zaten Muratpaşa'da - kullanıcı onu Aksu olarak istiyor olabilir
        # ya da o ayrı bir mahalle. 
        # Şimdi sadece Aksu'ya ekleyelim (geom'u Muratpaşa'dan al)
        if not any('ermenek' in n['name'].lower() for n in aksu['neighborhoods']):
            aksu_ermenek = dict(ermenek)
            aksu_ermenek['color'] = '#D53F8C'
            aksu['neighborhoods'].append(aksu_ermenek)
            print("Ermenek Muratpasa'dan Aksu'ya kopyalandı:", ermenek['name'])
    else:
        print("Ermenek Muratpaşa'da bulunamadı!")
        print("Muratpaşa mahalleleri:", [n['name'] for n in muratpasa['neighborhoods']])

print("Aksu mahalleleri:", [n['name'] for n in aksu['neighborhoods']])

with open(path, 'w', encoding='utf-8') as f:
    f.write('const database = ' + json.dumps(db, ensure_ascii=False) + ';')
print("Kaydedildi.")
