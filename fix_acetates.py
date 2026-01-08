
import json

def fix_smiles(smiles, drugs):
    # Fix Megestrol acetate (C17-OH -> C17-OAc)
    # Original pattern: CC(=O)[C@@]1(O)
    # Target pattern: CC(=O)[C@@]1(OC(=O)C)
    if 'Megestrol acetate' in drugs:
        smiles = smiles.replace('CC(=O)[C@@]1(O)', 'CC(=O)[C@@]1(OC(=O)C)')

    # Fix C21-acetates (Hydrocortisone, Prednisolone, Dexamethasone)
    # Original end: C(=O)CO
    # Target end: C(=O)COC(=O)C
    if any(x in drugs for x in ['Hydrocortisone acetate', 'Prednisolone acetate', 'Dexamethasone acetate']):
        if smiles.endswith('C(=O)CO'):
             smiles = smiles[:-7] + 'C(=O)COC(=O)C'
    
    return smiles

def main():
    try:
        data = json.load(open('src/data.json', encoding='utf-8'))
        targets = ['Megestrol acetate', 'Hydrocortisone acetate', 'Prednisolone acetate', 'Dexamethasone acetate']
        
        modified_count = 0
        for d in data:
            if d['en'] in targets:
                old_smiles = d['smiles']
                new_smiles = fix_smiles(old_smiles, d['en'])
                if old_smiles != new_smiles:
                    d['smiles'] = new_smiles
                    print(f"Fixed {d['en']}:\n  Old: {old_smiles}\n  New: {new_smiles}")
                    modified_count += 1
                else:
                    print(f"No change for {d['en']} (Pattern not found?)")
        
        if modified_count > 0:
            with open('src/data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved {modified_count} changes to src/data.json")
        else:
            print("No changes made.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
