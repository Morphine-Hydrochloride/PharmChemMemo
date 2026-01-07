import json
import os

SMILES_UPDATE = {
    "Lesinurad": "C1CC1C2=CC=C(C3=CC=CC=C23)N4C(=NN=C4Br)SCC(=O)O",
    "Chidamide": "FC1=CC(N)=C(NC(C2=CC=C(CNC(/C=C/C3=CC=CN=C3)=O)C=C2)=O)C=C1"
}

file_path = 'src/verified_smiles.json'

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
else:
    data = {}

updated_count = 0
for name, smiles in SMILES_UPDATE.items():
    if name not in data:
        data[name] = smiles
        updated_count += 1
        print(f"Added {name}")
    else:
        print(f"{name} already exists, skipping/updating...")
        # Optional: Force update if needed, but for now just skip if present
        # data[name] = smiles 

if updated_count > 0:
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Successfully added {updated_count} items to {file_path}")
else:
    print("No changes made.")
