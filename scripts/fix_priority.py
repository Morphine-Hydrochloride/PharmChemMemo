import requests
import json

drugs = {
    "Pentazocine": 441278,
    "Estazolam": 3261,
    "Zopiclone": 4036
}

results = {}
for name, cid in drugs.items():
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/CanonicalSMILES,IsomericSMILES/JSON"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Checking {name}...")
    if r.status_code == 200:
        data = r.json()
        props = data['PropertyTable']['Properties'][0]
        smiles = props.get('IsomericSMILES') or props.get('CanonicalSMILES')
        results[name] = smiles
        print(f"  > {smiles}")

# Apply to verified_smiles.json
with open('src/verified_smiles.json', 'r', encoding='utf-8') as f:
    verified = json.load(f)

for name, smiles in results.items():
    verified[name] = smiles

with open('src/verified_smiles.json', 'w', encoding='utf-8') as f:
    json.dump(verified, f, ensure_ascii=False, indent=4)

# Apply to data.json
with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for drug in data:
    en = drug.get("en")
    if en in results:
        drug["smiles"] = results[en]

with open('src/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated data.json and verified_smiles.json")
