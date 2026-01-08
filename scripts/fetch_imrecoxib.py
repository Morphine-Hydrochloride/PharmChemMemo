
import requests
import json

def get_pubchem_smiles(name):
    print(f"Querying PubChem for {name}...")
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IsomericSMILES/JSON"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            s = data['PropertyTable']['Properties'][0]['IsomericSMILES']
            return s
        else:
            print(f"Failed with status {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    return None

smiles = get_pubchem_smiles("Imrecoxib")
if smiles:
    print(f"FOUND: {smiles}")
else:
    print("NOT FOUND")
