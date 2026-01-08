
import json
import urllib.request
import urllib.parse
import time
import sys
import ssl

# The buggy DB (subset or full)
LOCAL_SMILES_DB = {
    # Chapter 5
    "Diazepam": "CN1C(=O)CN=C(C2=C1C=CC(=C2)Cl)C3=CC=CC=C3",
    "Estazolam": "C1C2=C(C=CC(=C2)Cl)N3C(=NN3)C(=N1)C4=CC=CC=C4",
    "Midazolam": "CC1=NC=C2N1C3=C(C=C(C=C3)Cl)C(=NC2)C4=CC=CC=C4F",
    "Zopiclone": "CN1CCN(CC1)C(=O)OC2C3=NC=CN3C(=O)C4=CC=CC=N24",
    "Zolpidem tartrate": "CC1=CC=C(C=C1)C2=C(N3C=C(C=C3N2)C)CC(=O)N(C)C", # Zolpidem base
    "Ramelteon": "CCC(=O)NCC1CCC2=C1C=CC3=C2OCC3",
    "Phenobarbital": "CCC1(C(=O)NC(=O)NC1=O)C2=CC=CC=C2",
    "Phenytoin sodium": "C1(C(=O)NC(=O)N1)C2=CC=CC=C2", # Phenytoin base
    "Carbamazepine": "C1=CC=C2C(=C1)C=CC3=CC=CC=C3N2C(=O)N",
    "Pregabalin": "CC(C)CC(CN)CC(=O)O",

    # Chapter 6
    "Chlorpromazine hydrochloride": "CN(C)CCCN1C2=CC=CC=C2SC3=C1C=C(C=C3)Cl", # Base
    "Perphenazine": "C1CN(CCN1CCCN2C3=CC=CC=C3SC4=C2C=C(C=C4)Cl)CCO",
    "Chlorprothixene": "CN(C)CC/C=C\\1/C2=CC=CC=C2SC3=C1C=C(C=C3)Cl",
    "Haloperidol": "C1CC(CCN1CCCC(=O)C2=CC=C(C=C2)F)(C3=CC=C(C=C3)Cl)O",
    "Sulpiride": "CCN1CCCC1CNC(=O)C2=C(C=CC(=C2)S(=O)(=O)N)OC",
    "Clozapine": "CN1CCN(CC1)C2=C(C=CC(=C2)Cl)NC3=CC=CC=C3N=C2",
    "Amitriptyline hydrochloride": "CN(C)CCC=C1C2=CC=CC=C2CCC3=CC=CC=C31", # Base
    "Escitalopram oxalate": "CN(C)CCCC1(C2=C(CO1)C=C(C=C2)C#N)C3=CC=C(C=C3)F", # Base

    # Chapter 8
    "Morphine hydrochloride": "CN1CCC23C4C1CC5=C2C(=C(C=C5)O)OC3C(C=C4)O", # Base
    "Pentazocine": "CC1=C(C2(CC1)CC(C(=C2)O)N(C)CC=C(C)C)C", # Approx
    "Pethidine hydrochloride": "CCN(CC)C(=O)C1CCN(CC1)C", # Meperidine base
    "Fentanyl citrate": "CCC(=O)N(C1=CC=CC=C1)C2CCN(CC2)CCC3=CC=CC=C3", # Base
    "Methadone hydrochloride": "CCC(=O)C(CC(C)N(C)C)(C1=CC=CC=C1)C2=CC=CC=C2", # Base
    "Tramadol": "CN(C)CC(C1=CC(=CC=C1)OC)C2(CCCCC2)O",

    # Chapter 9
    "Paracetamol": "CC(=O)NC1=CC=C(C=C1)O",
    "Aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
    "Indomethacin": "CC1=C(C2=C(N1C(=O)C3=CC=C(C=C3)Cl)C=CC(=C2)OC)CC(=O)O",
    "Diclofenac sodium": "C1=C(C(=C(C(=C1)Cl)NC2=C(C=CC=C2CC(=O)O)Cl)Cl)", # Acid
    "Ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
    "Naproxen": "CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)O",
    "Piroxicam": "CN1C(=C(C2=CC=CC=C2S1(=O)=O)O)C(=O)NC3=CC=CC=N3",
    "Allopurinol": "C1=C2C(=NC=N1)C(=O)NN2",

    # Chapter 18 (Antibiotics)
    "Penicillin G": "CC1(C(N2C(S1)C(C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C",
    "Amoxicillin": "CC1(C(N2C(S1)C(C2=O)NC(=O)C(C3=CC=C(C=C3)O)N)C(=O)O)C",
    "Cefalexin": "CC1=C(N2C(S1)C(C2=O)NC(=O)C(C3=CC=CC=C3)N)C(=O)O",
    "Chloramphenicol": "C1=CC(=CC=C1C(C(CO)NC(=O)C(Cl)Cl)O)[N+](=O)[O-]",

    # Chapter 19
    "Sulfamethoxazole": "CC1=CC(=NO1)NS(=O)(=O)C2=CC=C(C=C2)N",
    "Norfloxacin": "CCN1C=C(C(=O)C2=CC(=C(C=C21)N3CCNCC3)F)C(=O)O",
    "Ciprofloxacin": "C1CC1N2C=C(C(=O)C3=CC(=C(C=C32)N4CCNCC4)F)C(=O)O",
    "Levofloxacin": "CC1COC2=C3N1C=C(C(=O)C3=CC(=C2N4CCN(CC4)C)F)C(=O)O",
    "Isoniazid": "C1=CN=CC=C1C(=O)NN",
    "Fluconazole": "C1=CC(=C(C=C1F)C(CN2C=NC=N2)(CN3C=NC=N3)O)F",

    # Chapter 20
    "Acyclovir": "C1=NC2=C(N1COCCO)N=C(NC2=O)N",
    "Oseltamivir phosphate": "CCC(CC)OC1C=C(CC(C1NC(=O)C)N)C(=O)OCC", # Base
    "Ribavirin": "C1=C(N(C(=N1)C(=O)N)C2C(C(C(O2)CO)O)O)N",

    # Chapter 21
    "Cyclophosphamide": "C1CN(P(=O)(OC1)NCCCl)CCCl",
    "Cisplatin": "Cl[Pt](Cl)(N)N",
    "Methotrexate": "CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)NC(CCC(=O)O)C(=O)O",
    "Fluorouracil": "C1=C(C(=O)NC(=O)N1)F",
    "Imatinib mesylate": "CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)NC4=NC=CC(=N4)C5=CN=C(S5)N", # Base

    # Previous Manual Patches
    "Formestane": "C[C@]12CC[C@H]3[C@H]([C@@H]1CC[C@@H]2O)CCC4=CC(=O)C(O)=C[C@]34C",
    "Domperidone": "CC1=C(C(=O)N(C1=O)CCCCN2CCC(CC2)N3C(=O)NC4=CC=CC=C43)Cl"
}


def fetch_smiles(name):
    """Fetch Canonical SMILES from PubChem"""
    # Try removing salt names for better matching
    search_name = name.replace(" hydrochloride", "").replace(" hydrobromide", "").replace(" sodium", "") .replace(" citrate", "").replace(" tartrate", "").replace(" maleate", "").replace(" sulfate", "")
    
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(search_name)}/property/CanonicalSMILES/JSON"
    try:
        # Ignore SSL certificate errors
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
            data = json.loads(response.read().decode())
            smiles = data.get("PropertyTable", {}).get("Properties", [{}])[0].get("CanonicalSMILES")
            return smiles
    except Exception as e:
        print(f"Error fetching {name} ({search_name}): {e}")
        return None

def main():
    print("Fixing SMILES DB...")
    corrected_db = {}
    
    for name in LOCAL_SMILES_DB.keys():
        print(f"Checking {name}...", end=" ")
        smiles = fetch_smiles(name)
        if smiles:
            corrected_db[name] = smiles
            print(f"OK")
        else:
            print(f"FAILED - Keeping original")
            corrected_db[name] = LOCAL_SMILES_DB[name] # Fallback to what we have
        
        time.sleep(0.3) # Rate limit
    
    # Save the corrected DB to a file we can import/copy
    with open("corrected_smiles.json", "w", encoding="utf-8") as f:
        json.dump(corrected_db, f, indent=4)
    
    print("Done! Saved to corrected_smiles.json")

if __name__ == "__main__":
    main()
