
from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

db = {
    "Diazepam": "CN1C(=O)CN=C(C2=C1C=CC(=C2)Cl)C3=CC=CC=C3",
    "Estazolam": "C1C2=C(C=CC(=C2)Cl)N3C(=NN3)C(=N1)C4=CC=CC=C4", # Known Bad
    "Midazolam": "CC1=NC=C2N1C3=C(C=C(C=C3)Cl)C(=NC2)C4=CC=CC=C4F",
    "Zopiclone": "CN1CCN(CC1)C(=O)OC2C3=NC=CN3C(=O)C4=CC=CC=N24",
}

expectations = {
    "Diazepam": "C16H13ClN2O",
    "Estazolam": "C16H11ClN4",
    "Midazolam": "C18H13ClFN3",
    "Zopiclone": "C17H17ClN6O3", 
}

print(f"{'Drug':<15} | {'My Formula':<15} | {'Exp Formula':<15} | {'Match'}")
print("-" * 60)

for name, smiles in db.items():
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        formula = CalcMolFormula(mol)
        exp = expectations.get(name, "?")
        print(f"{name:<15} | {formula:<15} | {exp:<15} | {formula == exp}")
    else:
        print(f"{name:<15} | INVALID SMILES")
