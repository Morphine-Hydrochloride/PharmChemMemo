
import json
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Setup Robust Session
def get_session():
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    # Fake user agent just in case
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })
    return session

def fetch_nci_smiles(session, name):
    url = f"https://cactus.nci.nih.gov/chemical/structure/{name}/smiles"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            smiles = response.text.strip()
            if '\n' in smiles: smiles = smiles.split('\n')[0]
            # NCI sometimes returns HTML on error but status 200? Check if it looks like smiles
            if "<html" in smiles.lower(): return None
            return smiles
        elif response.status_code == 404:
            return "NOT_FOUND"
        else:
            return None
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return None

def main():
    print("Starting Robust NCI Verification...")
    
    with open('src/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    session = get_session()
    
    report = {
        "verified": [],
        "mismatches": [],
        "not_found": [],
        "errors": []
    }

    count = 0
    total = len(data)

    print(f"{'Name':<30} | {'Status':<15} | {'NCI SMILES'}")
    print("-" * 80)

    for item in data:
        en_name = item.get('en')
        local_smiles = item.get('smiles', "")
        
        if not en_name: continue
        count += 1
        
        # Strategy:
        # 1. Try exact English Name
        nci_result = fetch_nci_smiles(session, en_name)
        
        # 2. If Failed, try removing salt suffixes
        if nci_result == "NOT_FOUND" or nci_result is None:
             suffixes = [" hydrochloride", " hydrobromide", " sodium", " citrate", " tartrate", " maleate", " sulfate", " acetate", " phosphate", " mesylate", " besilate", " nitrate", " propionate"]
             clean_name = en_name
             found_suffix = False
             
             # remove stereo prefixes? (Like L- or D-?) maybe.
             
             for s in suffixes:
                if en_name.lower().endswith(s):
                    clean_name = en_name.replace(s, "").replace(s.upper(), "").replace(s.title(), "") # Case insensitive replace approx
                    # Better: case insensitive regex or just slice if match
                    # Simple slice:
                    if en_name.lower().endswith(s): 
                         clean_name = en_name[:len(en_name)-len(s)]
                    found_suffix = True
                    break
             
             if found_suffix and clean_name != en_name:
                 nci_result = fetch_nci_smiles(session, clean_name)
        
        if nci_result and nci_result != "NOT_FOUND":
            # Comparison (String Exact Match for now)
            # Ideally verify canonicalization matches
            # Let's trust NCI is "Reference"
            
            # Since we don't have RDKit to canonicalize LOCAL_SMILES to NCI format, 
            # we can use NCI to canonicalize LOCAL_SMILES too!
            
            canon_local = None
            if local_smiles:
                 canon_local = fetch_nci_smiles(session, local_smiles) # Send SMILES to NCI to get canonical SMILES out
            
            # If NCI failed to parse local smiles, it might differ or be invalid
            if not canon_local or canon_local == "NOT_FOUND":
                canon_local = local_smiles # Fallback to raw comparison
            
            if canon_local == nci_result:
                report['verified'].append(en_name)
                # print(f"{en_name:<30} | {'MATCH':<15}")
            else:
                print(f"{en_name:<30} | {'MISMATCH':<15} | NCI: {nci_result[:20]}...")
                report['mismatches'].append({
                    "name": en_name,
                    "local_raw": local_smiles,
                    "local_canon_nci": canon_local,
                    "nci_official": nci_result
                })
        else:
            print(f"{en_name:<30} | {'NOT FOUND':<15}")
            report['not_found'].append(en_name)

        if count % 10 == 0:
            print(f"Propagating... {count}/{total}")
        
        time.sleep(0.2) # Be kind

    with open('verification_report_nci_final.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print("Complete.")

if __name__ == "__main__":
    main()
