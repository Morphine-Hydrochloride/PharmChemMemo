import json
import os

FILE_PATH = r'c:\Users\24550\Downloads\不背药化V2.1\不背药化\local_project\src\verified_smiles.json'
NEW_SMILES = "C[C@@H]1[C@@H]2CC3=C([C@]1(CCN2CC=C(C)C)C)C=C(C=C3)O"

try:
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if 'Pentazocine' in data:
        print(f"Updating Pentazocine in verified_smiles.json")
        print(f"Old: {data['Pentazocine']}")
        data['Pentazocine'] = NEW_SMILES
        print(f"New: {data['Pentazocine']}")
        
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Success")
    else:
        print("Pentazocine not found in verified_smiles.json")
        
except Exception as e:
    print(f"Error: {e}")
