import json
import requests
import time
import os

# OPSIN API endpoint
OPSIN_URL = "https://opsin.ch.cam.ac.uk/opsin/"

def fetch_opsin_smiles(name):
    """Fetch SMILES from OPSIN for a given drug name."""
    try:
        # OPSIN expects the name as part of the URL path
        # We need to handle special characters properly, usually OPSIN handles spaces/standard URL encoding
        url = f"{OPSIN_URL}{name}.json"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("smiles")
        elif response.status_code == 404:
            return None
        else:
            # print(f"Error {response.status_code} for {name}")
            return None
    except Exception as e:
        print(f"Exception for {name}: {e}")
        return None

def normalize_smiles_simple(smiles):
    """Very basic string normalization used for exact match check if scientific normalization isn't available."""
    if not smiles: return ""
    return smiles.strip()

def main():
    print("Starting OPSIN Verification...")
    
    with open('src/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    report = {
        "verified": [],
        "mismatches": [],
        "not_found": [],
        "errors": []
    }

    count = 0
    total = len(data)

    print(f"{'Name':<30} | {'Status':<15} | {'OPSIN SMILES (truncated)'}")
    print("-" * 80)

    for item in data:
        en_name = item.get('en')
        local_smiles = item.get('smiles', "")
        
        if not en_name:
            continue
            
        count += 1
        
        # 1. Try exact English name
        opsin_smiles = fetch_opsin_smiles(en_name)
        
        # 2. If not found, try cleaning common salt suffixes that might confuse strict parsers if not standard
        # However, OPSIN is usually good with salts. But let's try base name if salt fails.
        if not opsin_smiles:
            suffixes = [" hydrochloride", " hydrobromide", " sodium", " citrate", " tartrate", " maleate", " sulfate", " acetate", " phosphate", " mesylate"]
            clean_name = en_name
            for s in suffixes:
                if en_name.lower().endswith(s):
                    clean_name = en_name[0:-len(s)]
                    break # Only remove one suffix
            
            if clean_name != en_name:
                 opsin_smiles = fetch_opsin_smiles(clean_name)

        if opsin_smiles:
            # Comparison Logic
            # Without RDKit, we can't do true canonical comparison.
            # We will flag it as mismatch if strings differ, user/we must review.
            if local_smiles == opsin_smiles:
                report['verified'].append(en_name)
                # print(f"{en_name:<30} | {'MATCH':<15}")
            else:
                print(f"{en_name:<30} | {'MISMATCH':<15} | {opsin_smiles[:30]}...")
                report['mismatches'].append({
                    "name": en_name,
                    "local": local_smiles,
                    "opsin": opsin_smiles
                })
        else:
            print(f"{en_name:<30} | {'NOT FOUND':<15}")
            report['not_found'].append(en_name)
        
        # Be nice to the server
        time.sleep(0.1)
        if count % 10 == 0:
            print(f"Progress: {count}/{total}")

    # Save full report
    with open('verification_report_opsin.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("-" * 80)
    print(f"Summary:")
    print(f"  Total Verified (Exact String Match): {len(report['verified'])}")
    print(f"  Mismatches (Needs Review):           {len(report['mismatches'])}")
    print(f"  Not Found in OPSIN:                  {len(report['not_found'])}")
    print(f"Report saved to verification_report_opsin.json")

if __name__ == "__main__":
    main()
