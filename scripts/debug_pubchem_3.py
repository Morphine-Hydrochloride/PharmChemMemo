import requests
import json

name = "Pentazocine"
url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Testing URL: {url}")
r = requests.get(url, headers=headers)
print(f"Status: {r.status_code}")
print(f"Content Type: {r.headers.get('Content-Type')}")
try:
    print(json.dumps(r.json(), indent=2))
except:
    print(f"Raw text: {r.text[:500]}")
