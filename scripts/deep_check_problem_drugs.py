#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深度检查问题药物 - 输出到 JSON"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    from rdkit.Chem.inchi import MolToInchi, InchiToInchiKey
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NON_MED_FILE = PROJECT_DIR / "src" / "非药化专业.json"
OUTPUT_FILE = SCRIPT_DIR / "deep_check_result.json"

PROBLEM_DRUGS = ["Maropitant", "Bedaquiline", "Osimertinib", "Canagliflozin"]


def get_pubchem(name, timeout=15):
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(name)}/property/IsomericSMILES,CanonicalSMILES,MolecularFormula,MolecularWeight,InChIKey/JSON"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('PropertyTable', {}).get('Properties', [{}])[0]
    except:
        return None


def analyze_smiles(smiles):
    if not RDKIT_AVAILABLE or not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return {"error": "parse_failed"}
        formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
        mw = round(Descriptors.MolWt(mol), 2)
        inchi = MolToInchi(mol)
        inchi_key = InchiToInchiKey(inchi) if inchi else None
        return {"formula": formula, "mw": mw, "inchi_key": inchi_key}
    except:
        return None


def main():
    with open(NON_MED_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    drug_map = {d.get('en', '').lower(): d for d in drugs}
    results = []
    
    for name in PROBLEM_DRUGS:
        result = {"en": name, "cn": "", "current_smiles": "", "pubchem_smiles": "",
                  "match": None, "issue": "", "recommendation": ""}
        
        current = drug_map.get(name.lower())
        if current:
            result["cn"] = current.get("cn", "")
            result["current_smiles"] = current.get("smiles", "")
        
        pubchem = get_pubchem(name)
        if pubchem:
            result["pubchem_smiles"] = pubchem.get("IsomericSMILES") or pubchem.get("CanonicalSMILES", "")
            result["pubchem_formula"] = pubchem.get("MolecularFormula", "")
            result["pubchem_mw"] = pubchem.get("MolecularWeight", "")
            result["pubchem_inchi_key"] = pubchem.get("InChIKey", "")
        
        # 对比
        if result["current_smiles"] and result["pubchem_smiles"]:
            cur = analyze_smiles(result["current_smiles"])
            pub = analyze_smiles(result["pubchem_smiles"])
            
            if cur and pub:
                result["current_formula"] = cur.get("formula")
                result["current_mw"] = cur.get("mw")
                result["current_inchi_key"] = cur.get("inchi_key")
                
                if cur.get("inchi_key") == pub.get("inchi_key"):
                    result["match"] = True
                    result["issue"] = "无问题 - InChI Key 完全匹配"
                elif cur.get("formula") == pub.get("formula"):
                    result["match"] = "partial"
                    result["issue"] = "分子式匹配，可能仅立体化学差异"
                else:
                    result["match"] = False
                    result["issue"] = f"分子式不匹配: 当前 {cur.get('formula')} vs PubChem {pub.get('formula')}"
                    result["recommendation"] = result["pubchem_smiles"]
        
        results.append(result)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
