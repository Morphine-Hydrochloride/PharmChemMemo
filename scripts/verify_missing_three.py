
import requests
import json
import time

drugs = ["Imrecoxib", "Prazosin", "Sofosbuvir"]

def get_smiles(name):
    # Try NCI
    try:
        url = f"https://cactus.nci.nih.gov/chemical/structure/{name}/smiles"
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and "<html" not in r.text.lower():
            return r.text.strip()
    except:
        pass
    
    # Try OPSIN (Cambridge) as backup
    try:
        url = f"https://opsin.ch.cam.ac.uk/opsin/{name}.json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get('smiles')
    except:
        pass
        
    return None

results = {}
for d in drugs:
    print(f"Fetching {d}...")
    s = get_smiles(d)
    if s:
        print(f"  Found: {s}")
        results[d] = s
    else:
        print(f"  NOT FOUND")

# Update verified_smiles.json
try:
    with open('src/verified_smiles.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
except:
    db = {}

# Be careful with Prazosin hydrochloride vs Prazosin
# The missing list had "Prazosin hydrochloride" but I searched "Prazosin".
# I should store it under "Prazosin hydrochloride" if that's the key, or "Prazosin" if I use base.
# The image gen script looks for base name too.
# Let's add both if possible or just the base.

db.update(results)
# Add mapped names
if "Prazosin" in results:
    db["Prazosin hydrochloride"] = results["Prazosin"]

with open('src/verified_smiles.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print("Updated verified_smiles.json")
