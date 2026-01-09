import json
import os

FILE_PATH = r'c:\Users\24550\Downloads\不背药化V2.1\不背药化\local_project\src\data.json'
# Correct SMILES for Pentazocine (standard isomer)
NEW_SMILES = "C[C@@H]1[C@@H]2CC3=C([C@]1(CCN2CC=C(C)C)C)C=C(C=C3)O"

try:
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    found = False
    for item in data:
        if item.get('cn') == '喷他佐辛' or item.get('en') == 'Pentazocine':
            print(f"Updating {item.get('cn')}")
            print(f"Old SMILES: {item.get('smiles')}")
            item['smiles'] = NEW_SMILES
            print(f"New SMILES: {item.get('smiles')}")
            found = True
            break
            
    if found:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Successfully updated data.json")
    else:
        print("Pentazocine not found in data.json")

except Exception as e:
    print(f"Error: {e}")
