
import json
import os

def check():
    print("--- CHECKING METHYLDOPA ---")
    
    # 1. Check verified_smiles.json
    try:
        with open('src/verified_smiles.json', 'r', encoding='utf-8') as f:
            v_db = json.load(f)
            v_smiles = v_db.get("Methyldopa", "NOT_FOUND")
            print(f"Verified DB SMILES: {v_smiles}")
            if "COC(=O)" in v_smiles:
                print("  STATUS: INCORRECT (Methyl Ester)")
            elif "C(O)=O" in v_smiles:
                print("  STATUS: CORRECT (Acid)")
            else:
                print("  STATUS: UNKNOWN PATTERN")
    except Exception as e:
        print(f"Error reading verified_smiles.json: {e}")

    # 2. Check data.json
    try:
        with open('src/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            target = [d for d in data if d.get('en') == 'Methyldopa']
            if target:
                d_smiles = target[0].get('smiles', 'MISSING')
                print(f"Data.json SMILES:   {d_smiles}")
                if "COC(=O)" in d_smiles:
                    print("  STATUS: INCORRECT (Methyl Ester)")
                elif "C(O)=O" in d_smiles:
                    print("  STATUS: CORRECT (Acid)")
                else:
                    print("  STATUS: UNKNOWN PATTERN")
            else:
                print("Data.json: Methyldopa NOT FOUND")
    except Exception as e:
        print(f"Error reading data.json: {e}")

    # 3. Check Image File
    try:
        svg_path = 'public/assets/images/Methyldopa.svg'
        if os.path.exists(svg_path):
            modified_time = os.path.getmtime(svg_path)
            from datetime import datetime
            print(f"Image Last Modified: {datetime.fromtimestamp(modified_time)}")
        else:
            print("Image File: NOT FOUND")
    except Exception as e:
        print(f"Error checking image: {e}")

if __name__ == "__main__":
    check()
