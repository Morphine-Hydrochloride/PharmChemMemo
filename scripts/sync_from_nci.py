
import json
import urllib.request
import urllib.parse
import time
import sys
import ssl
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_FILE = PROJECT_DIR / "src" / "data.json"
OUTPUT_FILE = PROJECT_DIR / "src" / "verified_smiles.json"

def fetch_nci_smiles(name):
    # Try removing salt names
    search_name = name.replace(" hydrochloride", "").replace(" hydrobromide", "").replace(" sodium", "") .replace(" citrate", "").replace(" tartrate", "").replace(" maleate", "").replace(" sulfate", "") .replace(" phosphate", "").replace(" besilate", "").replace(" nitrate", "").replace(" acetate", "")
    
    url = f"https://cactus.nci.nih.gov/chemical/structure/{urllib.parse.quote(search_name)}/smiles"
    try:
        # Ignore SSL
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
            smiles = response.read().decode().strip()
            if "\n" in smiles: smiles = smiles.split("\n")[0]
            if "<h1>" in smiles: return None
            return smiles
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return None

def main():
    print("Syncing ALL drugs from data.json with NCI CACTUS...")
    
    # 1. Read drug list from data.json
    if not DATA_FILE.exists():
        print(f"Error: {DATA_FILE} not found")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        drugs_data = json.load(f)
    
    drug_names = []
    for d in drugs_data:
        if d.get("en"):
            drug_names.append(d["en"].strip())
    
    # Remove duplicates
    drug_names = list(set(drug_names))
    print(f"Found {len(drug_names)} unique drugs in data.json")

    # 2. Load existing verified DB to resume/skip
    verified_db = {}
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            verified_db = json.load(f)
        print(f"Loaded {len(verified_db)} existing entries from verified_smiles.json")

    success = 0
    fail = 0
    skipped = 0
    
    for name in drug_names:
        # Skip if already verified (optional, but saves time. Set 'False' to force re-check)
        if name in verified_db and verified_db[name]: 
            skipped += 1
            print(f"Skipping {name} (already verified)")
            continue

        print(f"Fetching {name}...", end=" ")
        smiles = fetch_nci_smiles(name)
        if smiles:
            verified_db[name] = smiles
            print(f"OK")
            success += 1
        else:
            print(f"FAILED")
            fail += 1
        
        time.sleep(0.3)
    
    # 3. Apply Manual Fixes for known failures
    manual_fixes = {
        "Estazolam": "Clc1ccc2n3cnnc3CN=C(c4ccccc4)c2c1",
        "Zopiclone": "CN1CCN(CC1)C(=O)OC2N(C(=O)c3nccnc23)c4ccc(Cl)cn4"
    }
    for k, v in manual_fixes.items():
        verified_db[k] = v

    # 4. Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(verified_db, f, indent=4)
    
    print(f"\nCompleted. Fetched: {success}, Skipped: {skipped}, Fail: {fail}")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
