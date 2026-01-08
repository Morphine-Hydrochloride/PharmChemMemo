
import json

drugs = ["Zopiclone", "Imrecoxib"]

with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for drug in drugs:
    found = False
    for item in data:
        if item.get('en') == drug or item.get('cn') == drug:
             print(f"Name: {item.get('en')} | CN: {item.get('cn')}")
             print(f"Current SMILES: {item.get('smiles')}")
             found = True
             break
    if not found:
        print(f"{drug} NOT FOUND in data.json")
