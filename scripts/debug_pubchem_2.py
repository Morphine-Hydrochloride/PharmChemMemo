import requests
import json
import requests.utils

names = ["Diazepam", "Olanzapine", "Aspirin"]
for name in names:
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(name)}/property/CanonicalSMILES/JSON"
    print(f"Testing: {name}")
    print(f"URL: {url}")
    try:
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Text: {r.text[:200]}")
        data = r.json()
        smiles = data['PropertyTable']['Properties'][0].get('CanonicalSMILES')
        print(f"SMILES: {smiles}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
