import json
import os
import requests
import time
from pathlib import Path
from rdkit import Chem

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_FILE = PROJECT_DIR / "src" / "data.json"
VERIFIED_SMILES_FILE = PROJECT_DIR / "src" / "verified_smiles.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_json(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"  > [ERROR] {url} returned {res.status_code}")
            return None
    except Exception as e:
        print(f"  > [EXCEPT] {url} : {e}")
        return None

def get_pubchem_smiles(name):
    # CID
    cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(name)}/cids/JSON"
    cid_data = fetch_json(cid_url)
    if not cid_data:
        return None
    
    cid = cid_data.get('IdentifierList', {}).get('CID', [None])[0]
    if not cid:
        return None
        
    # SMILES
    smiles_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/CanonicalSMILES/JSON"
    smiles_data = fetch_json(smiles_url)
    if not smiles_data:
        return None
        
    return smiles_data.get('PropertyTable', {}).get('Properties', [{}])[0].get('CanonicalSMILES')

def canonicalize(smiles):
    if not smiles: return None
    try:
        smiles = smiles.split(' ')[0]
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            frags = Chem.GetMolFrags(mol, asMols=True)
            if frags:
                largest_mol = max(frags, key=lambda m: m.GetNumAtoms())
                return Chem.MolToSmiles(largest_mol, isomericSmiles=True)
    except: pass
    return None

def main():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    if VERIFIED_SMILES_FILE.exists():
        with open(VERIFIED_SMILES_FILE, 'r', encoding='utf-8') as f:
            verified_smiles = json.load(f)
    else:
        verified_smiles = {}

    mismatches = []
    missing = []

    print(f"Running sequential verification for 20 drugs as test...")
    for i, drug in enumerate(drugs[:50]): # test first 50
        en_name = drug.get("en", "").strip()
        cn_name = drug.get("cn", "").strip()
        local_smiles = drug.get("smiles") or verified_smiles.get(en_name)
        
        print(f"[{i+1}/50] {en_name}...", end=" ", flush=True)
        
        pubchem_smiles = get_pubchem_smiles(en_name)
        if not pubchem_smiles:
            print("FAILED")
            missing.append(en_name)
            continue
            
        canon_local = canonicalize(local_smiles)
        canon_pubchem = canonicalize(pubchem_smiles)
        
        if canon_local != canon_pubchem:
            print("MISMATCH")
            mismatches.append({"name": en_name, "cn": cn_name, "local": local_smiles, "pubchem": pubchem_smiles})
        else:
            print("OK")
        
        time.sleep(0.5)

    print(f"\nTest finished. Mismatches: {len(mismatches)}, Missing: {len(missing)}")
    if mismatches:
        print("\nMISMATCHES:")
        for m in mismatches:
            print(f" - {m['name']} ({m['cn']})")

if __name__ == "__main__":
    main()
