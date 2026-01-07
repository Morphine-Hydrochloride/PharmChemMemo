
import json
import requests
import time
import urllib.parse

def normalize(s):
    if not s: return ""
    return s.strip()

def fetch_pubchem_smiles(name):
    try:
        # PUG REST API
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(name)}/property/IsomericSMILES/JSON"
        # Using a timeout to prevent hanging, but generous enough for slow network
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if 'PropertyTable' in data:
                return data['PropertyTable']['Properties'][0]['IsomericSMILES']
    except Exception as e:
        # print(f"Error checking {name}: {e}")
        pass
    return None

def main():
    print("Starting Strict PubChem Verification (One by One)...")
    
    with open('src/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    report = {
        "mismatches": [],
        "not_found": [],
        "verified": []
    }
    
    total = len(data)
    for i, item in enumerate(data):
        name = item.get('en')
        local_smiles = normalize(item.get('smiles'))
        
        if not name: continue
        
        # Log progress clearly
        print(f"[{i+1}/{total}] Checking: {name}")
        
        pubchem_smiles = fetch_pubchem_smiles(name)
        
        # If not found directly, try cleaning salt name just in case PubChem is strict about mixture names
        # But user said "stupid search", so maybe exact mapping is better. 
        # Actually PubChem handles "Warfarin Sodium" usually.
        
        if not pubchem_smiles:
            # Fallback: Check Chinese name or Salt-stripped name?
            # Let's try salt stripped just to be thorough if direct failed
            suffixes = [" hydrochloride", " sodium", " sulfate", " phosphate", " maleate"]
            base = name
            for s in suffixes:
                if base.lower().endswith(s):
                    base = base[:len(base)-len(s)]
                    break
            if base != name:
                pubchem_smiles = fetch_pubchem_smiles(base)
        
        if pubchem_smiles:
            if local_smiles == pubchem_smiles:
                report['verified'].append(name)
            else:
                # Comparison might fail due to tautomers or different canonicalization
                # We save it for manual review
                print(f"  -> MISMATCH")
                print(f"     Local:   {local_smiles}")
                print(f"     PubChem: {pubchem_smiles}")
                report['mismatches'].append({
                    "name": name,
                    "local": local_smiles,
                    "pubchem": pubchem_smiles
                })
        else:
            print(f"  -> NOT FOUND in PubChem")
            report['not_found'].append(name)
        
        # Be nice to API
        time.sleep(0.5)

    with open('verification_report_strict.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("Verification Complete.")
    print(f"Verified: {len(report['verified'])}")
    print(f"Mismatches: {len(report['mismatches'])}")
    print(f"Not Found: {len(report['not_found'])}")

if __name__ == "__main__":
    main()
