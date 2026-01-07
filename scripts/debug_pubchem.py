import requests
import json
name = "Olanzapine"
url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/CanonicalSMILES/JSON"
r = requests.get(url)
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))
