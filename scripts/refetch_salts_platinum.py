#!/usr/bin/env python3
"""
重新抓取特定药物的 InChI (保留盐形式和金属配合物)
修复之前因去除后缀导致获取到游离酸的问题 (如苯妥英钠 -> 苯妥英)
"""
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
from pathlib import Path

# 禁用SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

# 路径
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR.parent / 'src' / 'data.json'
INCHI_CACHE_FILE = SCRIPT_DIR.parent / 'src' / 'inchi_cache.json'

def get_pubchem_inchi_exact(drug_name_en):
    """
    通过精确英文名从PubChem获取InChI (不清理后缀)
    """
    print(f"正在获取: {drug_name_en} ...", end=' ', flush=True)
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(drug_name_en)}/property/InChI,MolecularFormula/JSON"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            props = data['PropertyTable']['Properties'][0]
            print("✓")
            return {
                'inchi': props.get('InChI', ''),
                'formula': props.get('MolecularFormula', '')
            }
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}")
        return {'error': f'HTTP {e.code}'}
    except Exception as e:
        print(f"✗ {str(e)[:50]}")
        return {'error': str(e)[:100]}

def main():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    with open(INCHI_CACHE_FILE, 'r', encoding='utf-8') as f:
        inchi_cache = json.load(f)
        
    updated_count = 0
    
    # 需要特殊处理的关键词
    target_keywords = [
        " sodium", " potassium", " calcium", " magnesium", # 盐类
        "cisplatin", "carboplatin", "oxaliplatin", "nedaplatin", "lobaplatin" # 铂类
    ]
    
    for drug in drugs:
        en_name = drug['en']
        en_lower = en_name.lower()
        
        # 检查是否是目标药物
        is_target = any(k in en_lower for k in target_keywords)
        
        if is_target:
            # 强制重新获取精确匹配的 InChI
            result = get_pubchem_inchi_exact(en_name)
            
            if 'inchi' in result:
                new_inchi = result['inchi']
                drug['inchi'] = new_inchi
                inchi_cache[en_name] = new_inchi # 更新缓存
                updated_count += 1
                
                # 顺便检查一下分子式
                print(f"  -> Formula: {result.get('formula')}")
            
            time.sleep(0.5)
            
    # 保存更新
    if updated_count > 0:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(drugs, f, ensure_ascii=False, indent=2)
        with open(INCHI_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(inchi_cache, f, ensure_ascii=False, indent=2)
        print(f"\n成功更新了 {updated_count} 个药物的 InChI。")
    else:
        print("\n没有需要更新的药物。")

if __name__ == '__main__':
    main()
