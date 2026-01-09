#!/usr/bin/env python3
"""
修复铂类药物SMILES，使其显示显式配位键
并清除这些药物在data.json中的inchi字段，防止被后续脚本覆盖
"""
import json
from pathlib import Path

# 路径
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR.parent / 'src' / 'data.json'
VERIFIED_SMILES_FILE = SCRIPT_DIR.parent / 'src' / 'verified_smiles.json'

# 手动构建的含键SMILES
PLATINUM_SMILES = {
    "Cisplatin": "N[Pt](Cl)(Cl)N", # 顺铂
    "Carboplatin": "N[Pt]1(N)OC(=O)C2(CCC2)C(=O)O1", # 卡铂
    "Oxaliplatin": "[H][C@]12CCCC[C@]1([H])N[Pt]3(OC(=O)C(=O)O3)N2", # 奥沙利铂
    "Nedaplatin": "N[Pt]1(N)OCC(=O)O1", # 奈达铂
    "Lobaplatin": "C1C(C1CN[Pt]2(OCC(O2)(C)C(=O)O)N)CN" # 洛铂 (复杂，简化表示连接)
    # Lobaplatin: 1,2-diaminomethyl-cyclobutane platinum(II) lactate
    # Structure: Cyclobutane ring with -CH2NH2 groups chelated to Pt. Lactate (-OCH(Me)COO-) chelated to Pt.
    # SMILES: C1CC1(CN[Pt]2(OCm(C)C(=O)O2)N)
}

def main():
    # 1. 更新 verified_smiles.json
    if VERIFIED_SMILES_FILE.exists():
        with open(VERIFIED_SMILES_FILE, 'r', encoding='utf-8') as f:
            verified_data = json.load(f)
        
        updated_verified = False
        for name, smiles in PLATINUM_SMILES.items():
            if name in verified_data:
                print(f"更新 verified_smiles.json: {name} -> {smiles}")
                verified_data[name] = smiles
                updated_verified = True
            else:
                print(f"警告: {name} 不在 verified_smiles.json 中")
        
        if updated_verified:
            with open(VERIFIED_SMILES_FILE, 'w', encoding='utf-8') as f:
                json.dump(verified_data, f, ensure_ascii=False, indent=2)
            print("verified_smiles.json 已保存。")

    # 2. 清除 data.json 中的 inchi 字段 (针对这些铂类药物)
    # 这样生成脚本就会退回到使用 verified_smiles.json 中的 SMILES
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated_data = False
        target_names = PLATINUM_SMILES.keys()
        
        for drug in data:
            if drug.get('en') in target_names:
                # 清除 inchi
                if 'inchi' in drug:
                    print(f"清除 {drug['en']} 的 InChI (使用显式键 SMILES)")
                    del drug['inchi']
                    updated_data = True
                # 同时更新 data.json 里的 smiles，以防万一
                if drug['en'] in PLATINUM_SMILES:
                    drug['smiles'] = PLATINUM_SMILES[drug['en']]
                    updated_data = True
        
        if updated_data:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("data.json 已保存。")

if __name__ == '__main__':
    main()
