
import json

def normalize_smiles(s):
    if not s: return ""
    return s.strip()

with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('src/verified_smiles.json', 'r', encoding='utf-8') as f:
    verified = json.load(f)

print(f"{'Name':<30} | {'Status':<10} | {'Details'}")
print("-" * 80)

mismatches = 0
missing_in_verified = 0

for item in data:
    en = item.get('en')
    smiles = normalize_smiles(item.get('smiles'))
    
    if not en: continue
    
    # Try finding in verified
    v_smiles = verified.get(en)
    if not v_smiles:
        # Try stripping salt
        base = en.replace(" hydrochloride", "").replace(" sodium", "")
        v_smiles = verified.get(base)
    
    if v_smiles:
        v_smiles = normalize_smiles(v_smiles)
        if smiles != v_smiles:
            print(f"{en:<30} | MISMATCH   | Data: {smiles[:15]}... != Veri: {v_smiles[:15]}...")
            mismatches += 1
    else:
        print(f"{en:<30} | MISSING    | Not in verified_smiles.json")
        missing_in_verified += 1

print("-" * 80)
print(f"Total Mismatches: {mismatches}")
print(f"Total Missing in Verified DB: {missing_in_verified}")
