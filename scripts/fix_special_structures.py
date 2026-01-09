#!/usr/bin/env python3
"""
修复特殊药物的SMILES结构：
1. 铂类药物：显示显式配位键 (Cisplatin, Carboplatin, Oxaliplatin)
2. 苯妥英钠：显示2号位烯醇钠形式 (-O-Na)
并清除这些药物在data.json中的inchi字段，防止被后续脚本覆盖
"""
import json
from pathlib import Path

# 路径
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR.parent / 'src' / 'data.json'
VERIFIED_SMILES_FILE = SCRIPT_DIR.parent / 'src' / 'verified_smiles.json'

# 手动构建的特殊SMILES
SPECIAL_SMILES = {
    # 铂类 - 显式连接
    "Cisplatin": "N[Pt](Cl)(Cl)N", 
    "Carboplatin": "N[Pt]1(N)OC(=O)C2(CCC2)C(=O)O1",
    "Oxaliplatin": "[H][C@]12CCCC[C@]1([H])N[Pt]3(OC(=O)C(=O)O3)N2",
    "Nedaplatin": "N[Pt]1(N)OCC(=O)O1",
    
    # 苯妥英钠 - 2号位烯醇钠形式 (Ionic)
    # 结构：C2-[O-] [Na+], C4=O, N1-H
    # 使用离散离子表示，CoordGen 通常会将其放置在 O- 附近
    "Phenytoin sodium": "[Na+].[O-]C1=NC(=O)C(c2ccccc2)(c3ccccc3)[NH]1"
}

def main():
    # 1. 更新 verified_smiles.json
    if VERIFIED_SMILES_FILE.exists():
        with open(VERIFIED_SMILES_FILE, 'r', encoding='utf-8') as f:
            verified_data = json.load(f)
        
        updated_verified = False
        for name, smiles in SPECIAL_SMILES.items():
            verified_data[name] = smiles
            print(f"设定Verified SMILES: {name} -> {smiles}")
            updated_verified = True
        
        if updated_verified:
            with open(VERIFIED_SMILES_FILE, 'w', encoding='utf-8') as f:
                json.dump(verified_data, f, ensure_ascii=False, indent=2)
            print("verified_smiles.json 已保存。")

    # 2. 清除 data.json 中的 inchi 字段 (针对这些药物)
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated_data = False
        target_names = SPECIAL_SMILES.keys()
        
        for drug in data:
            if drug.get('en') in target_names:
                # 清除 inchi，强迫使用 verified_smiles
                if 'inchi' in drug:
                    print(f"清除 {drug['en']} 的 InChI")
                    del drug['inchi']
                    updated_data = True
                
                # 同步更新 smiles
                if drug.get('smiles') != SPECIAL_SMILES[drug['en']]:
                    drug['smiles'] = SPECIAL_SMILES[drug['en']]
                    updated_data = True
                    print(f"更新 {drug['en']} 的 SMILES")
        
        if updated_data:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("data.json 已保存。")

if __name__ == '__main__':
    main()
