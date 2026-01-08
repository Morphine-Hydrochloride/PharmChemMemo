#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复有问题的药物 SMILES

根据 PubChem 权威数据修正以下药物:
1. 马罗匹坦 (Maropitant)
2. 贝达喹啉 (Bedaquiline)
3. 奥希替尼 (Osimertinib)
4. 卡格列净 (Canagliflozin)
"""

import json
from pathlib import Path

try:
    from rdkit import Chem
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NON_MED_FILE = PROJECT_DIR / "src" / "非药化专业.json"

# PubChem 验证过的正确 SMILES
CORRECTIONS = {
    "Maropitant": {
        "correct_smiles": "CC(C)(C)C1=CC(=C(C=C1)OC)CN[C@@H]2[C@@H](N3CCC2CC3)C(C4=CC=CC=C4)C5=CC=CC=C5",
        "notes": "PubChem CID: 6450555, 分子式: C32H40N2O"
    },
    "Bedaquiline": {
        "correct_smiles": "CN(C)CC[C@@](C1=CC=CC2=CC=CC=C21)([C@H](C3=CC=CC=C3)C4=C(N=C5C=CC(=CC5=C4)Br)OC)O",
        "notes": "PubChem CID: 5388906, 分子式: C32H31BrN2O2"
    },
    "Osimertinib": {
        "correct_smiles": "CN1C=C(C2=CC=CC=C21)C3=NC(=NC=C3)NC4=C(C=C(C(=C4)NC(=O)C=C)N(C)CCN(C)C)OC",
        "notes": "PubChem CID: 71496458, 分子式: C28H33N7O2"
    },
    "Canagliflozin": {
        "correct_smiles": "CC1=C(C=C(C=C1)[C@@H]2[C@@H]([C@H]([C@@H]([C@H](O2)CO)O)O)O)CC3=CC=C(S3)C4=CC=C(C=C4)F",
        "notes": "PubChem CID: 24812758, 分子式: C24H25FO5S"
    }
}


def validate_smiles(smiles):
    """验证 SMILES 是否有效"""
    if not RDKIT_AVAILABLE:
        return True
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except:
        return False


def main():
    print("=" * 70)
    print("修复有问题的药物 SMILES")
    print("=" * 70)
    
    # 加载数据
    with open(NON_MED_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    # 建立索引
    drug_index = {}
    for i, drug in enumerate(drugs):
        en_name = drug.get('en', '').strip()
        drug_index[en_name.lower()] = i
    
    fixed_count = 0
    
    for drug_name, correction in CORRECTIONS.items():
        print(f"\n【{drug_name}】")
        
        idx = drug_index.get(drug_name.lower())
        if idx is None:
            print(f"  ⚠ 未找到该药物")
            continue
        
        drug = drugs[idx]
        old_smiles = drug.get('smiles', '')
        new_smiles = correction['correct_smiles']
        
        # 验证新 SMILES
        if not validate_smiles(new_smiles):
            print(f"  ⚠ 新 SMILES 无效，跳过")
            continue
        
        print(f"  中文名: {drug.get('cn', '')}")
        print(f"  旧 SMILES: {old_smiles[:50]}...")
        print(f"  新 SMILES: {new_smiles[:50]}...")
        print(f"  来源: {correction['notes']}")
        
        if old_smiles != new_smiles:
            drugs[idx]['smiles'] = new_smiles
            fixed_count += 1
            print(f"  ✓ 已修复")
        else:
            print(f"  ○ 无需修改")
    
    # 保存
    if fixed_count > 0:
        with open(NON_MED_FILE, 'w', encoding='utf-8') as f:
            json.dump(drugs, f, ensure_ascii=False, indent=2)
        print(f"\n{'=' * 70}")
        print(f"完成！共修复 {fixed_count} 个药物")
        print(f"数据已保存到: {NON_MED_FILE}")
        print(f"\n请重新运行图像生成脚本更新这些药物的分子结构图像。")
    else:
        print(f"\n无需修复")


if __name__ == "__main__":
    main()
