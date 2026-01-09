import json
import re

def get_keys():
    with open('src/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        data_keys = {item['en']: item['cn'] for item in data}
    
    with open('src/keyPointsData.js', 'r', encoding='utf-8') as f:
        content = f.read()
        kp_keys = re.findall(r'"([^"]+)": \[', content)
        kp_keys = set(kp_keys)
    
    return data_keys, kp_keys

data_keys, kp_keys = get_keys()

print("--- Mismatched (In data.json but NOT in keyPointsData.js) ---")
for en, cn in data_keys.items():
    if en not in kp_keys:
        # Check if it exists in KP with a different name (simple check)
        norm_en = en.replace(' hydrochloride', '').replace(' sodium', '').replace(' tartrate', '').replace(' nitrate', '')
        if norm_en in kp_keys:
            print(f"[NOMATCH_BUT_SIMILAR] {cn} | Card: '{en}' | KP: '{norm_en}'")
        else:
            # Check if it's a 'master' drug - these are the important ones
            pass

print("\n--- Orphaned (In keyPointsData.js but NOT in data.json) ---")
for en in kp_keys:
    if en not in data_keys:
        print(f"[ORPHAN] '{en}'")
