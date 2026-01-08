import json

# Correct SMILES from PubChem
updates = {
    "Estazolam": "ClC1=CC2=C(C=C1)N3C=NN=C3CN=C2C4=CC=CC=C4",
    "Zopiclone": "CN1CCN(CC1)C(=O)OC2N3C(=O)C4=C(C3=NC2C5=CC=C(C=N5)Cl)N=CC=N4",
    "Pentazocine": "CC=C(C)C1CC2Cc3ccc(O)cc3[C@]1(C)C2"
}

with open('src/data.json', 'r', encoding='utf-8') as f:
    drugs = json.load(f)

for drug in drugs:
    en = drug.get("en")
    if en in updates:
        drug["smiles"] = updates[en]
        print(f"Updated {en}")

with open('src/data.json', 'w', encoding='utf-8') as f:
    json.dump(drugs, f, ensure_ascii=False, indent=2)

print("data.json updated successfully.")
