
import json
import os
from pathlib import Path

# Correct SMILES found via NCI/Web Search
FIXES = {
    "Zopiclone": "CN1CCN(CC1)C(=O)OC2C3=NC=CN=C3C(=O)N2C4=NC=C(C=C4)Cl",
    "Imrecoxib": "CCCN1CC(=C(C1=O)C2=CC=C(C=C2)C)C3=CC=C(C=C3)S(=O)(=O)C"
}

DATA_PATH = Path('src/data.json')
VERIFIED_PATH = Path('src/verified_smiles.json')

def update_json_file(path, updates, is_list=False):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated = False
    if is_list:
        for item in data:
            name = item.get('en')
            if name in updates:
                print(f"Updating {name} in {path}...")
                item['smiles'] = updates[name]
                # Reset image path to force refresh if needed, roughly
                # item['image'] = ... (regenerator handles this)
                updated = True
    else:
        # Dictionary (verified_smiles.json)
        for name, smiles in updates.items():
            if data.get(name) != smiles:
                print(f"Updating {name} in {path}...")
                data[name] = smiles
                updated = True
                
    if updated:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {path}")
    else:
        print(f"No changes needed for {path}")

# 1. Update data files
print("Applying SMILES fixes...")
update_json_file(DATA_PATH, FIXES, is_list=True)
update_json_file(VERIFIED_PATH, FIXES, is_list=False)

# 2. Run image generator (it will pick up the changes from data.json or verified_smiles.json)
# We can just run the existing script
print("Regenerating images...")
os.system("python scripts/generate_molecule_images.py")
