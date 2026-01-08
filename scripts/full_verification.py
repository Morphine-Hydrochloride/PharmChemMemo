import json
import os
import requests
import time
from pathlib import Path
from rdkit import Chem
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_FILE = PROJECT_DIR / "src" / "data.json"
VERIFIED_SMILES_FILE = PROJECT_DIR / "src" / "verified_smiles.json"

def get_cactus_smiles(name):
    """Fetch SMILES from NCI CACTUS by name."""
    try:
        url = f"https://cactus.nci.nih.gov/chemical/structure/{requests.utils.quote(name)}/smiles"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.text.strip()
        return None
    except Exception:
        return None

def canonicalize(smiles):
    """Canonicalize SMILES using RDKit."""
    if not smiles:
        return None
    try:
        # Cleanup
        smiles = smiles.split(' ')[0]
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            # Remove salts/fragments and keep largest
            frags = Chem.GetMolFrags(mol, asMols=True)
            if frags:
                largest_mol = max(frags, key=lambda m: m.GetNumAtoms())
                return Chem.MolToSmiles(largest_mol, isomericSmiles=True)
    except:
        pass
    return None

def process_drug(drug, verified_smiles):
    en_name = drug.get("en", "").strip()
    cn_name = drug.get("cn", "").strip()
    
    local_smiles = drug.get("smiles")
    if not local_smiles:
        local_smiles = verified_smiles.get(en_name)
    
    if not en_name:
        return None

    # Try name directly from CACTUS
    official_smiles = get_cactus_smiles(en_name)
    
    # Try removing salt suffixes if not found
    if not official_smiles:
        salts = [" hydrochloride", " sodium", " tartrate", " besilate", " maleate", " citrate", " sulfate", " phosphate", " acetate", " nitrate", " bromide", " mesylate", " hydrobromide", " fumarate", " succinate", " oxalate"]
        base_name = en_name
        for salt in salts:
            if salt in base_name.lower():
                base_name = base_name.lower().replace(salt, "").strip().capitalize()
                break
        
        if base_name != en_name:
            official_smiles = get_cactus_smiles(base_name)

    if not official_smiles:
        return {"status": "missing", "name": en_name, "cn": cn_name}

    canon_local = canonicalize(local_smiles)
    canon_official = canonicalize(official_smiles)

    if canon_local != canon_official:
        return {
            "status": "mismatch",
            "name": en_name,
            "cn": cn_name,
            "local": local_smiles,
            "official": official_smiles,
            "canon_local": canon_local,
            "canon_official": canon_official
        }
    
    return {"status": "ok", "name": en_name}

def main():
    if not DATA_FILE.exists():
        print(f"File not found: {DATA_FILE}")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    if VERIFIED_SMILES_FILE.exists():
        with open(VERIFIED_SMILES_FILE, 'r', encoding='utf-8') as f:
            verified_smiles = json.load(f)
    else:
        verified_smiles = {}

    print(f"Verifying {len(drugs)} drugs via NCI CACTUS...")

    mismatches = []
    missing = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_drug = {executor.submit(process_drug, drug, verified_smiles): drug for drug in drugs}
        done_count = 0
        for future in as_completed(future_to_drug):
            res = future.result()
            if res:
                if res["status"] == "missing":
                    missing.append(res["name"])
                elif res["status"] == "mismatch":
                    mismatches.append(res)
                
                done_count += 1
                if done_count % 10 == 0:
                    print(f"Progress: {done_count}/{len(drugs)}...")

    # Final report
    print("\n" + "="*50)
    print("VERIFICATION REPORT")
    print("="*50)
    print(f"Total Drugs Checked: {len(drugs)}")
    print(f"Mismatches Found:    {len(mismatches)}")
    print(f"Missing in CACTUS:   {len(missing)}")
    
    if mismatches:
        print("\nTOP 20 MISMATCHES:")
        for m in mismatches[:20]:
            print(f"- {m['name']} ({m['cn']})")
    
    if missing:
        print(f"\nMissing first 10: {missing[:10]}")
            
    # Save results
    report = {
        "mismatches": mismatches,
        "missing": missing,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(PROJECT_DIR / "verification_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\nDetailed report saved to verification_report.json")

if __name__ == "__main__":
    main()
