
import json

def fix_verified_db():
    try:
        data_path = 'src/verified_smiles.json'
        with open(data_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
            
        updates = {
            "Methyldopa": "N[C@@](C)(Cc1ccc(O)c(O)c1)C(O)=O",
            "Megestrol acetate": "CC(=O)O[C@@]1(C(C)=O)CC[C@H]2[C@@H]3C=C(C)C4=CC(=O)CC[C@]4(C)[C@H]3CC[C@]12C",
            "Hydrocortisone acetate": "C[C@]12CCC(=O)C=C1CC[C@H]3[C@@H]4CC[C@](O)(C(=O)COC(=O)C)[C@@]4(C)C[C@H](O)[C@H]23",
            "Prednisolone acetate": "C[C@]12C[C@H](O)[C@H]3[C@@H](CCC4=CC(=O)C=C[C@]34C)[C@@H]1CC[C@]2(O)C(=O)COC(=O)C",
            "Dexamethasone acetate": "C[C@@H]1C[C@H]2[C@@H]3CCC4=CC(=O)C=C[C@]4(C)[C@@]3(F)[C@@H](O)C[C@]2(C)[C@@]1(O)C(=O)COC(=O)C"
        }
        
        count = 0
        for name, smiles in updates.items():
            if name in db:
                if db[name] != smiles:
                    print(f"Updating {name} in verified DB...")
                    db[name] = smiles
                    count += 1
            else:
                print(f"Adding {name} to verified DB...")
                db[name] = smiles
                count += 1
                
        if count > 0:
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            print(f"Successfully updated verified_smiles.json with {count} fixes.")
        else:
            print("verified_smiles.json is already up to date.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_verified_db()
