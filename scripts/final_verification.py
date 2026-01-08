import json

with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

targets = ["erythromycin", "lesinurad", "chidamide"]
fl = {t: False for t in targets}

print("Verification Report:")
for item in data:
    en = item.get('en', '').lower()
    cn = item.get('cn', '')
    
    # Check Erythromycin
    if "erythromycin" in en or "红霉素" in cn:
        print(f"[Erythromycin] Image: {item.get('image')}")
        fl['erythromycin'] = True
        
    # Check Lesinurad
    if "lesinurad" in en:
        print(f"[Lesinurad] SMILES: {item.get('smiles')[:20]}... | Image: {item.get('image')}")
        fl['lesinurad'] = True
        
    # Check Chidamide
    if "chidamide" in en or "西达本胺" in cn:
        print(f"[Chidamide] SMILES: {item.get('smiles')[:20]}... | Image: {item.get('image')}")
        fl['chidamide'] = True

for k, v in fl.items():
    if not v:
        print(f"WARNING: {k} was not found in data.json!")
