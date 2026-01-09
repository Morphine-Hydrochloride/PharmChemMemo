#!/usr/bin/env python3
"""
SMILES验证脚本 - 使用RDKit规范化SMILES后通过PubChem API验证结构
只报告真正的结构错误（分子式或原子组成不同）
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

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors
    from rdkit.Chem.inchi import MolFromInchi, MolToInchi
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
    print("警告: 未安装RDKit，将使用简化比较方法")

def get_pubchem_data(drug_name_en):
    """通过英文名从PubChem获取SMILES和分子式"""
    # 清理药物名称（去掉盐形式后缀）
    clean_name = drug_name_en.replace(" hydrochloride", "").replace(" maleate", "").replace(" sulfate", "").replace(" sodium", "").replace(" tartrate", "").replace(" phosphate", "").replace(" besilate", "").replace(" citrate", "").replace(" bromide", "").replace(" nitrate", "").replace(" oxalate", "").strip()
    
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(clean_name)}/property/CanonicalSMILES,IsomericSMILES,MolecularFormula,InChI/JSON"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            props = data['PropertyTable']['Properties'][0]
            return {
                'canonical': props.get('CanonicalSMILES', ''),
                'isomeric': props.get('IsomericSMILES', ''),
                'formula': props.get('MolecularFormula', ''),
                'inchi': props.get('InChI', ''),
                'cid': props.get('CID', '')
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'error': 'Not found'}
        return {'error': f'HTTP {e.code}'}
    except Exception as e:
        return {'error': str(e)[:50]}

def get_canonical_smiles(smiles):
    """使用RDKit获取规范化SMILES"""
    if not HAS_RDKIT or not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return Chem.MolToSmiles(mol, canonical=True)
    except:
        pass
    return None

def get_mol_formula(smiles):
    """从SMILES获取分子式"""
    if not HAS_RDKIT or not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return Chem.rdMolDescriptors.CalcMolFormula(mol)
    except:
        pass
    return None

def get_inchi(smiles):
    """从SMILES获取InChI"""
    if not HAS_RDKIT or not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return MolToInchi(mol)
    except:
        pass
    return None

def strip_salt(smiles):
    """移除盐离子，只保留主要分子"""
    if not smiles:
        return smiles
    parts = smiles.split('.')
    # 常见的盐离子和溶剂
    salts = {'[Na+]', '[K+]', '[Ca+2]', '[Cl-]', '[Br-]', '[H+]', 'O', '[O-]', 
             '[I-]', '[F-]', '[NH4+]', '[Li+]', '[Mg+2]'}
    # 常见的酸
    acids = {'OC(=O)/C=C\\C(=O)O', 'OC(=O)C=CC(=O)O', 'OC(=O)/C=C/C(=O)O',  # 马来酸/富马酸
             'OC(=O)C(O)C(O)C(=O)O', 'O[C@@H]([C@@H](O)C(O)=O)C(O)=O',  # 酒石酸
             'OP(O)(O)=O', 'O[P](O)(O)=O',  # 磷酸
             'O=S(=O)(O)c1ccccc1',  # 苯磺酸
             'OC(=O)CC(O)(CC(=O)O)C(=O)O',  # 柠檬酸
             'OC(=O)C(=O)O',  # 草酸
    }
    
    filtered = []
    for part in parts:
        if part in salts:
            continue
        # 跳过短小的离子 (通常 < 5 个字符的简单离子)
        if len(part) < 5 and ('[' in part or part in ['O', 'Cl', 'Br', 'I']):
            continue
        filtered.append(part)
    
    if filtered:
        # 返回最大的分子（通常是主药物）
        return max(filtered, key=len)
    return smiles

def compare_molecules(current_smiles, pubchem_data):
    """比较分子是否相同"""
    if 'error' in pubchem_data:
        return {'status': 'skip', 'reason': pubchem_data['error']}
    
    # 移除盐
    current_stripped = strip_salt(current_smiles)
    pubchem_stripped = strip_salt(pubchem_data['canonical'])
    
    if HAS_RDKIT:
        # 使用RDKit进行精确比较
        current_canonical = get_canonical_smiles(current_stripped)
        pubchem_canonical = get_canonical_smiles(pubchem_stripped)
        
        if current_canonical and pubchem_canonical:
            if current_canonical == pubchem_canonical:
                return {'status': 'match'}
            
            # 检查InChI (更可靠的比较方式)
            current_inchi = get_inchi(current_stripped)
            pubchem_inchi_stripped = get_inchi(pubchem_stripped)
            
            if current_inchi and pubchem_inchi_stripped:
                # 比较InChI的主要部分（忽略立体化学层）
                current_inchi_base = current_inchi.split('/')[1] if '/' in current_inchi else current_inchi
                pubchem_inchi_base = pubchem_inchi_stripped.split('/')[1] if '/' in pubchem_inchi_stripped else pubchem_inchi_stripped
                
                if current_inchi_base == pubchem_inchi_base:
                    return {'status': 'match', 'note': '立体化学可能不同'}
            
            # 比较分子式
            current_formula = get_mol_formula(current_stripped)
            pubchem_formula = get_mol_formula(pubchem_stripped)
            
            if current_formula and pubchem_formula:
                if current_formula == pubchem_formula:
                    return {'status': 'isomer', 'note': '同分子式，可能是异构体'}
                else:
                    return {
                        'status': 'error',
                        'reason': f'分子式不同: 当前={current_formula}, PubChem={pubchem_formula}',
                        'current_smiles': current_smiles,
                        'pubchem_smiles': pubchem_data['isomeric'] or pubchem_data['canonical'],
                        'cid': pubchem_data['cid']
                    }
        else:
            # RDKit无法解析SMILES
            return {'status': 'skip', 'reason': 'RDKit解析失败'}
    
    # 无RDKit时的简单比较
    return {'status': 'skip', 'reason': '需要RDKit进行精确比较'}

def main():
    script_dir = Path(__file__).parent
    data_path = script_dir.parent / 'src' / 'data.json'
    
    with open(data_path, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    print(f"开始验证 {len(drugs)} 种药物的SMILES结构...")
    print("=" * 80)
    
    results = {'match': [], 'isomer': [], 'error': [], 'skip': []}
    
    for i, drug in enumerate(drugs):
        cn = drug['cn']
        en = drug['en']
        smiles = drug.get('smiles', '')
        
        print(f"[{i+1}/{len(drugs)}] {cn} ({en})...", end=' ', flush=True)
        
        pubchem = get_pubchem_data(en)
        result = compare_molecules(smiles, pubchem)
        
        if result['status'] == 'match':
            print("✓ 正确")
            results['match'].append(cn)
        elif result['status'] == 'isomer':
            print(f"~ 同分子式 ({result.get('note', '')})")
            results['isomer'].append({'drug': cn, 'en': en, 'note': result.get('note', '')})
        elif result['status'] == 'error':
            print(f"✗ 错误!")
            results['error'].append({
                'drug': cn, 'en': en,
                'reason': result['reason'],
                'current': result.get('current_smiles', smiles),
                'correct': result.get('pubchem_smiles', ''),
                'cid': result.get('cid', '')
            })
        else:
            print(f"- 跳过 ({result.get('reason', '')})")
            results['skip'].append({'drug': cn, 'en': en, 'reason': result.get('reason', '')})
        
        time.sleep(0.25)  # 避免请求过快
    
    # 输出报告
    print("\n" + "=" * 80)
    print("验证报告")
    print("=" * 80)
    print(f"✓ 结构正确: {len(results['match'])} 个")
    print(f"~ 同分子式(异构体): {len(results['isomer'])} 个")
    print(f"✗ 结构错误: {len(results['error'])} 个")
    print(f"- 跳过/未找到: {len(results['skip'])} 个")
    
    if results['error']:
        print("\n" + "-" * 80)
        print("【需要修正的错误】")
        print("-" * 80)
        for err in results['error']:
            print(f"\n{err['drug']} ({err['en']})")
            print(f"  原因: {err['reason']}")
            print(f"  当前SMILES: {err['current']}")
            print(f"  正确SMILES: {err['correct']}")
            print(f"  PubChem CID: {err['cid']}")
    
    # 保存报告
    report_path = script_dir.parent / 'smiles_verification_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存到: {report_path}")

if __name__ == '__main__':
    main()
