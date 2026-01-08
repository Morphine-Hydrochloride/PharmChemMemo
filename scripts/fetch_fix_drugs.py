
import requests
import json
import time

drugs = ["Zopiclone", "Imrecoxib"]

def get_smiles(name):
    print(f"Searching for {name}...")
    # 1. NCI
    try:
        url = f"https://cactus.nci.nih.gov/chemical/structure/{name}/smiles"
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and "<html" not in r.text.lower():
            print(f"  [NCI] Found: {r.text.strip()}")
            return r.text.strip()
    except Exception as e:
        print(f"  [NCI] Error: {e}")

    # 2. PubChem (fallback, since user said it's slow, but for 2 drugs it's fine)
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IsomericSMILES/JSON"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            s = data['PropertyTable']['Properties'][0]['IsomericSMILES']
            print(f"  [PubChem] Found: {s}")
            return s
    except Exception as e:
        print(f"  [PubChem] Error: {e}")
        
    return None

results = {}
for d in drugs:
    s = get_smiles(d)
    if s:
        results[d] = s

print("-" * 30)
print("RESULTS:")
print(json.dumps(results, indent=2))
