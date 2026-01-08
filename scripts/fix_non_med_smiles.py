#!/usr/bin/env python3
"""
非药化专业 SMILES 修复脚本

优先从以下来源获取正确的 SMILES：
1. verified_smiles.json (最可靠 - NCI 验证过)
2. data.json 中的同名药物
3. PubChem API (在线获取)

然后更新 非药化专业.json 中的 SMILES 字段
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NON_MED_FILE = PROJECT_DIR / "src" / "非药化专业.json"
VERIFIED_SMILES_FILE = PROJECT_DIR / "src" / "verified_smiles.json"
DATA_FILE = PROJECT_DIR / "src" / "data.json"

# 盐酸盐/药盐后缀列表
SALT_SUFFIXES = [
    " hydrochloride", " hydrobromide", " sodium", " tartrate", " besilate",
    " maleate", " citrate", " sulfate", " phosphate", " acetate", " nitrate",
    " bromide", " mesylate", " fumarate", " succinate", " oxide", " calcium",
    " potassium", " dihydrate", " monohydrate", " trihydrate"
]


def load_json(filepath):
    """加载 JSON 文件"""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_json(filepath, data):
    """保存 JSON 文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def strip_salt_suffix(name):
    """移除药物名称中的盐后缀"""
    lower_name = name.lower()
    for suffix in SALT_SUFFIXES:
        if lower_name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def fetch_pubchem_smiles(name, timeout=10):
    """从 PubChem 获取正规 SMILES（使用 IsomericSMILES）"""
    try:
        encoded_name = urllib.parse.quote(name)
        # 使用 IsomericSMILES 获取保留立体化学信息的 SMILES
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/IsomericSMILES/JSON"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            smiles = data.get('PropertyTable', {}).get('Properties', [{}])[0].get('IsomericSMILES')
            return smiles
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # 未找到
        print(f"    PubChem HTTP 错误 ({name}): {e.code}")
        return None
    except Exception as e:
        print(f"    PubChem 请求失败 ({name}): {e}")
        return None


def fetch_nci_smiles(name, timeout=10):
    """从 NCI CACTUS 获取 SMILES（备用）"""
    try:
        encoded_name = urllib.parse.quote(name)
        url = f"https://cactus.nci.nih.gov/chemical/structure/{encoded_name}/smiles"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            smiles = response.read().decode('utf-8').strip()
            # NCI 可能返回多行，取第一个
            if '\n' in smiles:
                smiles = smiles.split('\n')[0]
            return smiles if smiles and not smiles.startswith('<') else None
    except Exception:
        return None


def main():
    print("=" * 70)
    print("非药化专业 SMILES 修复脚本")
    print("=" * 70)
    
    # 加载数据
    non_med_data = load_json(NON_MED_FILE)
    if not non_med_data:
        print(f"错误: 找不到 {NON_MED_FILE}")
        sys.exit(1)
    
    verified_smiles = load_json(VERIFIED_SMILES_FILE) or {}
    print(f"已加载 verified_smiles.json: {len(verified_smiles)} 个条目")
    
    data_json = load_json(DATA_FILE) or []
    # 建立 data.json 的查找索引
    data_smiles_map = {}
    for item in data_json:
        en = item.get('en', '')
        smiles = item.get('smiles', '')
        if en and smiles:
            data_smiles_map[en.lower()] = smiles
            # 也添加去掉盐后缀的版本
            base_name = strip_salt_suffix(en)
            if base_name.lower() != en.lower():
                data_smiles_map[base_name.lower()] = smiles
    print(f"已加载 data.json: {len(data_smiles_map)} 个条目")
    
    print(f"\n共 {len(non_med_data)} 个非药化专业药物需要处理")
    print("-" * 70)
    
    # 统计
    stats = {
        'from_verified': 0,
        'from_data_json': 0,
        'from_pubchem': 0,
        'from_nci': 0,
        'unchanged': 0,
        'not_found': 0,
        'errors': []
    }
    
    updated_data = []
    
    for i, drug in enumerate(non_med_data):
        en_name = drug.get('en', '')
        cn_name = drug.get('cn', '')
        old_smiles = drug.get('smiles', '')
        
        if not en_name:
            updated_data.append(drug)
            continue
        
        new_smiles = None
        source = None
        
        # 1. 优先从 verified_smiles.json 查找
        if en_name in verified_smiles:
            new_smiles = verified_smiles[en_name]
            source = "verified_smiles.json"
            stats['from_verified'] += 1
        else:
            # 尝试去掉盐后缀
            base_name = strip_salt_suffix(en_name)
            if base_name in verified_smiles:
                new_smiles = verified_smiles[base_name]
                source = "verified_smiles.json (base)"
                stats['from_verified'] += 1
        
        # 2. 从 data.json 查找
        if not new_smiles:
            lookup_key = en_name.lower()
            if lookup_key in data_smiles_map:
                new_smiles = data_smiles_map[lookup_key]
                source = "data.json"
                stats['from_data_json'] += 1
            else:
                base_name = strip_salt_suffix(en_name)
                if base_name.lower() in data_smiles_map:
                    new_smiles = data_smiles_map[base_name.lower()]
                    source = "data.json (base)"
                    stats['from_data_json'] += 1
        
        # 3. 从 PubChem 在线获取
        if not new_smiles:
            print(f"[{i+1}/{len(non_med_data)}] {cn_name} | {en_name} -> 从 PubChem 获取...")
            new_smiles = fetch_pubchem_smiles(en_name)
            
            if not new_smiles:
                # 尝试去掉盐后缀
                base_name = strip_salt_suffix(en_name)
                if base_name != en_name:
                    print(f"    尝试 base name: {base_name}")
                    new_smiles = fetch_pubchem_smiles(base_name)
            
            if new_smiles:
                source = "PubChem"
                stats['from_pubchem'] += 1
            
            time.sleep(0.3)  # 礼貌延迟
        
        # 4. 从 NCI CACTUS 备用获取
        if not new_smiles:
            print(f"    从 NCI CACTUS 获取...")
            new_smiles = fetch_nci_smiles(en_name)
            
            if not new_smiles:
                base_name = strip_salt_suffix(en_name)
                if base_name != en_name:
                    new_smiles = fetch_nci_smiles(base_name)
            
            if new_smiles:
                source = "NCI CACTUS"
                stats['from_nci'] += 1
            
            time.sleep(0.3)
        
        # 更新或保留
        if new_smiles:
            if new_smiles != old_smiles:
                print(f"[{i+1}/{len(non_med_data)}] ✓ {cn_name} | {en_name}")
                print(f"    来源: {source}")
                if old_smiles:
                    print(f"    旧: {old_smiles[:50]}{'...' if len(old_smiles) > 50 else ''}")
                print(f"    新: {new_smiles[:50]}{'...' if len(new_smiles) > 50 else ''}")
            else:
                stats['unchanged'] += 1
            
            drug['smiles'] = new_smiles
        else:
            print(f"[{i+1}/{len(non_med_data)}] ✗ {cn_name} | {en_name} - 未找到 SMILES!")
            stats['not_found'] += 1
            stats['errors'].append(en_name)
        
        updated_data.append(drug)
    
    # 保存更新后的数据
    print("\n" + "=" * 70)
    print("保存更新后的数据...")
    save_json(NON_MED_FILE, updated_data)
    print(f"已保存到 {NON_MED_FILE}")
    
    # 打印统计
    print("\n" + "=" * 70)
    print("统计:")
    print(f"  从 verified_smiles.json 获取: {stats['from_verified']}")
    print(f"  从 data.json 获取: {stats['from_data_json']}")
    print(f"  从 PubChem 获取: {stats['from_pubchem']}")
    print(f"  从 NCI CACTUS 获取: {stats['from_nci']}")
    print(f"  未变化: {stats['unchanged']}")
    print(f"  未找到: {stats['not_found']}")
    
    if stats['errors']:
        print(f"\n未能获取 SMILES 的药物:")
        for name in stats['errors']:
            print(f"  - {name}")
    
    print("\n完成！")
    print("请运行图像生成脚本重新生成分子结构图像。")


if __name__ == "__main__":
    main()
