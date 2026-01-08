import requests
import json

drugs = {
    "Pentazocine": 441278,
    "Estazolam": 3261,
    "Zopiclone": 4036
}

results = {}
for name, cid in drugs.items():
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/CanonicalSMILES/JSON"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if r.status_code == 200:
        smiles = r.json()['PropertyTable']['Properties'][0]['CanonicalSMILES']
        results[name] = smiles
        print(f"{name}: {smiles}")

with open('verified_priority.json', 'w') as f:
    json.dump(results, f, indent=2)
