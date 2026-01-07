
import urllib.request
import urllib.parse
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

drugs = ["Aspirin", "Oxazepam", "Diazepam", "Phenytoin sodium"]

for drug in drugs:
    print(f"Testing {drug}...")
    url = f"https://cactus.nci.nih.gov/chemical/structure/{urllib.parse.quote(drug)}/smiles"
    try:
        start = time.time()
        with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
            smiles = response.read().decode('utf-8').strip()
            print(f"  SUCCESS ({time.time()-start:.2f}s): {smiles}")
    except Exception as e:
        print(f"  FAILURE ({time.time()-start:.2f}s): {e}")
