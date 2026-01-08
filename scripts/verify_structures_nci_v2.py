
import json
import urllib.request
import urllib.parse
import time
import ssl
import sys
import os

# Contexto SSL para evitar errores de certificado
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_nci_smiles(query):
    """
    Fetch SMILES from NCI Resolver for a given query (name or SMILES).
    Returns the canonical SMILES string or None if not found.
    """
    if not query:
        return None
    
    # Try multiple variations if it's a name?
    # For now just precise query
    encoded_query = urllib.parse.quote(query)
    url = f"https://cactus.nci.nih.gov/chemical/structure/{encoded_query}/smiles"
    
    try:
        with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
            smiles = response.read().decode('utf-8').strip()
            # NCI can return multiple lines, take the first one usually
            if '\n' in smiles:
                smiles = smiles.split('\n')[0]
            return smiles
    except Exception as e:
        # print(f"Error fetching {query}: {e}")
        return None

def main():
    data_path = 'src/data.json'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filter for medicinal chemistry drugs only? 
    # Usually "chapter" field exists.
    # The user said "medicinal chemistry major", which likely implies all drugs in data.json (which is the main db)
    # non_med_data.json is for the other major.
    
    report = {
        "mismatches": [],
        "errors": [],
        "verified": []
    }

    print(f"{'Drug Name':<30} | {'Status':<15} | {'Details'}")
    print("-" * 80)

    # Process a subset for testing or all? 
    # Let's do all. It might take a while.
    # To be safe, maybe we should cache results or just run it.
    
    for item in data:
        en_name = item.get('en')
        local_smiles = item.get('smiles')
        
        if not en_name:
            continue
            
        # Clean name for search (remove salt info usually helps for NCI if full name fails, 
        # but NCI is good with full names too. Let's try full name first)
        
        # 1. Get Official SMILES from NCI by Name
        official_smiles = get_nci_smiles(en_name)
        
        if not official_smiles:
            # Try cleaning name
            dirty_suffices = [" hydrochloride", " hydrobromide", " sodium", " citrate", " tartrate", " maleate", " sulfate", " acetate", " phosphate"]
            clean_name = en_name
            for s in dirty_suffices:
                clean_name = clean_name.replace(s, "")
            
            if clean_name != en_name:
                official_smiles = get_nci_smiles(clean_name)

        if not official_smiles:
            print(f"{en_name:<30} | {'NOT FOUND':<15} | NCI did not return a structure")
            report['errors'].append(en_name)
            continue

        # 2. Canonicalize Local SMILES via NCI (to handle format diffs without RDKit)
        if local_smiles:
            canon_local = get_nci_smiles(local_smiles)
        else:
            canon_local = None

        # 3. Canonicalize Official SMILES via NCI (ensure same normalization)
        # It's already from NCI, but inputting it back ensures we get the *canonical* output for that string
        # actually the first call returns what NCI considers SMILES. 
        # But `get_nci_smiles` on an arbitrary SMILES might return a different string (the unique canonical one).
        canon_official = get_nci_smiles(official_smiles)
        
        if not canon_official:
            canon_official = official_smiles # Fallback

        if not canon_local:
             # If local SMILES is invalid or NCI can't parse it
             print(f"{en_name:<30} | {'INVALID LOCAL':<15} | Local SMILES could not be parsed by NCI")
             report['mismatches'].append({
                 "name": en_name,
                 "reason": "Local SMILES invalid or unparseable by NCI",
                 "local": local_smiles,
                 "official": official_smiles
             })
             continue

        # 4. Compare
        if canon_local == canon_official:
            # print(f"{en_name:<30} | {'MATCH':<15} | OK")
            report['verified'].append(en_name)
        else:
            print(f"{en_name:<30} | {'MISMATCH':<15} | Local vs Official mismatch")
            # print(f"   Local:    {local_smiles}")
            # print(f"   Official: {official_smiles}")
            report['mismatches'].append({
                "name": en_name,
                "local_canon": canon_local,
                "official_canon": canon_official,
                "local_raw": local_smiles,
                "official_raw": official_smiles
            })
        
        # Polite delay
        time.sleep(0.2)

    # Save Report
    with open('verification_report_nci.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("-" * 80)
    print(f"Verification finished.")
    print(f"Verified: {len(report['verified'])}")
    print(f"Mismatches: {len(report['mismatches'])}")
    print(f"Errors/Not Found: {len(report['errors'])}")
    print("See verification_report_nci.json for details.")

if __name__ == "__main__":
    main()
