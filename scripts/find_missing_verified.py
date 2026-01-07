
import json

with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('src/verified_smiles.json', 'r', encoding='utf-8') as f:
    verified = json.load(f)

missing = []
for item in data:
    en = item.get('en')
    if not en: continue
    
    # Check exact
    if en in verified: continue
    
    # Check base
    suffixes = [" hydrochloride", " hydrobromide", " sodium", " citrate", " tartrate", " maleate", " sulfate", " acetate", " phosphate", " mesylate", " besilate", " nitrate", " propionate"]
    base = en
    for s in suffixes:
        if base.lower().endswith(s):
             base = base[:len(base)-len(s)]
             break
    
    if base in verified: continue
    
    missing.append(en)

print("Missing from Verified DB:")
for m in missing:
    print(m)
