
import json

def fix_data():
    try:
        data = json.load(open('src/data.json', encoding='utf-8'))
        count = 0
        
        # 1. Fix Methyldopa (Ester -> Acid)
        # Target incorrect: COC(=O)[C@@H](N)Cc1ccc(O)c(O)c1
        # Target correct:   N[C@@](C)(Cc1ccc(O)c(O)c1)C(O)=O
        for d in data:
            if d['en'] == 'Methyldopa':
                if 'COC(=O)' in d['smiles']:
                    d['smiles'] = 'N[C@@](C)(Cc1ccc(O)c(O)c1)C(O)=O'
                    print("Fixed Methyldopa")
                    count += 1
            
            # 2. Fix Steroid Acetates (Alcohol -> Acetate Ester)
            # Hydrocortisone acetate, Prednisolone acetate, Dexamethasone acetate
            if d['en'] in ['Hydrocortisone acetate', 'Prednisolone acetate', 'Dexamethasone acetate']:
                if d['smiles'].endswith('C(=O)CO'):
                    d['smiles'] = d['smiles'][:-7] + 'C(=O)COC(=O)C'
                    print(f"Fixed {d['en']}")
                    count += 1
            
            # 3. Fix Megestrol acetate (Alcohol -> Acetate Ester)
            if d['en'] == 'Megestrol acetate':
                # Old: CC(=O)[C@@]1(O)...
                # New: CC(=O)[C@@]1(OC(C)=O)... OR just replace the specific part
                if 'CC(=O)[C@@]1(O)' in d['smiles']:
                     d['smiles'] = d['smiles'].replace('CC(=O)[C@@]1(O)', 'CC(=O)[C@@]1(OC(=O)C)')
                     print("Fixed Megestrol acetate")
                     count += 1

        if count > 0:
            with open('src/data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Successfully fixed {count} entries.")
        else:
            print("No entries needed fixing (already correct?).")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_data()
