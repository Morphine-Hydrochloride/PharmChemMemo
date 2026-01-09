import json
from pathlib import Path
from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize

# Load InChI Cache
cache_file = Path('src/inchi_cache.json')
with open(cache_file, 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Targets to check (likely to have tautomer issues)
targets = [
    "Fluorouracil", "Phenobarbital", "Acyclovir", "Zidovudine", 
    "Theophylline", "Uric Acid", "Phenytoin"
]

enumerator = rdMolStandardize.TautomerEnumerator()

print(f"{'Drug Name':<20} | {'Status':<10} | {'Original SMILES (from InChI)':<50} | {'Canonicalized Tautomer'}")
print("-" * 150)

for drug_name in targets:
    # Find in cache (partial match)
    inchi = None
    found_key = ""
    for k, v in cache.items():
        if drug_name.lower() in k.lower():
            inchi = v
            found_key = k
            break
            
    if not inchi:
        print(f"{drug_name:<20} | Not Found  |")
        continue

    print(f"--- {found_key} ---")

    mol = Chem.MolFromInchi(inchi)
    if not mol:
        print(f"{drug_name:<20} | Invalid InChI |")
        continue

    # 1. Direct conversion
    try:
        smiles_direct = Chem.MolToSmiles(mol)
    except:
        smiles_direct = "Error"
        
    # 2. Canonicalize Tautomer
    try:
        # Standardize first (remove fragments etc if needed, but here just tautomer)
        canonical_mol = enumerator.Canonicalize(mol)
        smiles_canonical = Chem.MolToSmiles(canonical_mol)
    except Exception as e:
        smiles_canonical = f"Error: {e}"

    # Check for Enol indicators (simplified: "O" in aromatic ring often implies -OH if not carbonyl)
    # Actually, visual inspection of SMILES is better:
    # Keto: C(=O)
    # Enol: c(O)n or C(O)=C
    
    output_line = f"{drug_name:<20} | {found_key:<20} | {smiles_direct} | {smiles_canonical}\n"
    print(output_line)
    with open('diagnosis_output.txt', 'a', encoding='utf-8') as f_out:
        f_out.write(output_line)

