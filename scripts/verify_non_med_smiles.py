#!/usr/bin/env python3
"""
非药化专业 SMILES 多源核查脚本

对比以下权威数据库:
1. PubChem (NIH) - 最权威的化学数据库
2. NCI CACTUS (NCI) - 美国国家癌症研究所
3. ChEMBL (EBI) - 欧洲生物信息学研究所
4. DrugBank (可选)

使用 RDKit 进行结构标准化对比
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors
    from rdkit.Chem.inchi import MolFromInchi, MolToInchi
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    print("警告: RDKit 未安装，将使用简单字符串对比")

# 路径配置
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NON_MED_FILE = PROJECT_DIR / "src" / "非药化专业.json"
REPORT_FILE = SCRIPT_DIR / "smiles_verification_report.txt"

# 盐酸盐/药盐后缀列表
SALT_SUFFIXES = [
    " hydrochloride", " hydrobromide", " sodium", " tartrate", " besilate",
    " maleate", " citrate", " sulfate", " phosphate", " acetate", " nitrate",
    " bromide", " mesylate", " fumarate", " succinate", " oxide", " calcium",
    " potassium", " dihydrate", " monohydrate", " trihydrate"
]


def strip_salt_suffix(name):
    """移除药物名称中的盐后缀"""
    lower_name = name.lower()
    for suffix in SALT_SUFFIXES:
        if lower_name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def canonicalize_smiles(smiles):
    """使用 RDKit 标准化 SMILES"""
    if not RDKIT_AVAILABLE or not smiles:
        return smiles
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return Chem.MolToSmiles(mol, canonical=True)
    except:
        pass
    return smiles


def get_inchi_key(smiles):
    """获取 InChI Key 用于精确对比"""
    if not RDKIT_AVAILABLE or not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            inchi = MolToInchi(mol)
            if inchi:
                from rdkit.Chem.inchi import InchiToInchiKey
                return InchiToInchiKey(inchi)
    except:
        pass
    return None


def get_molecular_formula(smiles):
    """获取分子式"""
    if not RDKIT_AVAILABLE or not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return Chem.rdMolDescriptors.CalcMolFormula(mol)
    except:
        pass
    return None


def fetch_pubchem_data(name, timeout=15):
    """从 PubChem 获取化合物数据"""
    try:
        encoded_name = urllib.parse.quote(name)
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/IsomericSMILES,CanonicalSMILES,MolecularFormula,InChIKey/JSON"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            props = data.get('PropertyTable', {}).get('Properties', [{}])[0]
            return {
                'source': 'PubChem',
                'isomeric_smiles': props.get('IsomericSMILES'),
                'canonical_smiles': props.get('CanonicalSMILES'),
                'molecular_formula': props.get('MolecularFormula'),
                'inchi_key': props.get('InChIKey')
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return None
    except Exception as e:
        return None


def fetch_nci_smiles(name, timeout=10):
    """从 NCI CACTUS 获取 SMILES"""
    try:
        encoded_name = urllib.parse.quote(name)
        url = f"https://cactus.nci.nih.gov/chemical/structure/{encoded_name}/smiles"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            smiles = response.read().decode('utf-8').strip()
            if '\n' in smiles:
                smiles = smiles.split('\n')[0]
            if smiles and not smiles.startswith('<'):
                return {'source': 'NCI CACTUS', 'smiles': smiles}
    except:
        pass
    return None


def fetch_chembl_data(name, timeout=15):
    """从 ChEMBL 获取化合物数据"""
    try:
        encoded_name = urllib.parse.quote(name)
        url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/search?q={encoded_name}&format=json"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            molecules = data.get('molecules', [])
            if molecules:
                mol = molecules[0]
                structs = mol.get('molecule_structures', {})
                return {
                    'source': 'ChEMBL',
                    'canonical_smiles': structs.get('canonical_smiles'),
                    'standard_inchi_key': structs.get('standard_inchi_key')
                }
    except:
        pass
    return None


def compare_smiles(smiles1, smiles2):
    """对比两个 SMILES 是否代表相同分子"""
    if not smiles1 or not smiles2:
        return None, "无法对比"
    
    # 1. 直接字符串对比
    if smiles1 == smiles2:
        return True, "完全匹配"
    
    if not RDKIT_AVAILABLE:
        return False, "字符串不匹配"
    
    try:
        mol1 = Chem.MolFromSmiles(smiles1)
        mol2 = Chem.MolFromSmiles(smiles2)
        
        if not mol1 or not mol2:
            return None, "SMILES解析失败"
        
        # 2. 标准化 SMILES 对比
        canon1 = Chem.MolToSmiles(mol1, canonical=True)
        canon2 = Chem.MolToSmiles(mol2, canonical=True)
        
        if canon1 == canon2:
            return True, "标准化后匹配"
        
        # 3. InChI Key 对比 (最精确)
        inchi1 = MolToInchi(mol1)
        inchi2 = MolToInchi(mol2)
        
        if inchi1 and inchi2:
            from rdkit.Chem.inchi import InchiToInchiKey
            key1 = InchiToInchiKey(inchi1)
            key2 = InchiToInchiKey(inchi2)
            
            if key1 and key2:
                # 对比连接层 (前14位)
                if key1[:14] == key2[:14]:
                    if key1 == key2:
                        return True, "InChI Key 完全匹配"
                    else:
                        return True, "InChI Key 连接层匹配 (立体化学可能不同)"
        
        # 4. 分子式和原子数对比
        formula1 = Chem.rdMolDescriptors.CalcMolFormula(mol1)
        formula2 = Chem.rdMolDescriptors.CalcMolFormula(mol2)
        
        if formula1 != formula2:
            return False, f"分子式不同: {formula1} vs {formula2}"
        
        # 分子式相同但结构不同
        return False, f"分子式相同但结构不同"
        
    except Exception as e:
        return None, f"对比出错: {e}"


def verify_drug(drug_name, current_smiles):
    """验证单个药物的 SMILES"""
    results = {
        'name': drug_name,
        'current_smiles': current_smiles,
        'sources': [],
        'status': 'unknown',
        'issues': []
    }
    
    # 获取当前 SMILES 的标准化信息
    if RDKIT_AVAILABLE and current_smiles:
        results['current_canonical'] = canonicalize_smiles(current_smiles)
        results['current_inchi_key'] = get_inchi_key(current_smiles)
        results['current_formula'] = get_molecular_formula(current_smiles)
    
    # 从多个来源获取数据
    names_to_try = [drug_name]
    base_name = strip_salt_suffix(drug_name)
    if base_name != drug_name:
        names_to_try.append(base_name)
    
    pubchem_data = None
    nci_data = None
    chembl_data = None
    
    for name in names_to_try:
        if not pubchem_data:
            pubchem_data = fetch_pubchem_data(name)
            if pubchem_data:
                results['sources'].append(pubchem_data)
                time.sleep(0.3)
        
        if not nci_data:
            nci_data = fetch_nci_smiles(name)
            if nci_data:
                results['sources'].append(nci_data)
                time.sleep(0.2)
        
        if not chembl_data:
            chembl_data = fetch_chembl_data(name)
            if chembl_data:
                results['sources'].append(chembl_data)
                time.sleep(0.2)
    
    # 对比分析
    matches = 0
    mismatches = 0
    
    if pubchem_data:
        pubchem_smiles = pubchem_data.get('isomeric_smiles') or pubchem_data.get('canonical_smiles')
        if pubchem_smiles:
            match, reason = compare_smiles(current_smiles, pubchem_smiles)
            if match is True:
                matches += 1
                results['pubchem_match'] = True
            elif match is False:
                mismatches += 1
                results['pubchem_match'] = False
                results['issues'].append(f"PubChem 不匹配: {reason}")
                results['pubchem_smiles'] = pubchem_smiles
    
    if nci_data:
        nci_smiles = nci_data.get('smiles')
        if nci_smiles:
            match, reason = compare_smiles(current_smiles, nci_smiles)
            if match is True:
                matches += 1
                results['nci_match'] = True
            elif match is False:
                mismatches += 1
                results['nci_match'] = False
                results['issues'].append(f"NCI CACTUS 不匹配: {reason}")
                results['nci_smiles'] = nci_smiles
    
    if chembl_data:
        chembl_smiles = chembl_data.get('canonical_smiles')
        if chembl_smiles:
            match, reason = compare_smiles(current_smiles, chembl_smiles)
            if match is True:
                matches += 1
                results['chembl_match'] = True
            elif match is False:
                mismatches += 1
                results['chembl_match'] = False
                results['issues'].append(f"ChEMBL 不匹配: {reason}")
                results['chembl_smiles'] = chembl_smiles
    
    # 确定状态
    if mismatches > 0:
        results['status'] = 'mismatch'
    elif matches >= 2:
        results['status'] = 'verified'
    elif matches == 1:
        results['status'] = 'partial'
    else:
        results['status'] = 'not_found'
    
    return results


def main():
    print("=" * 80)
    print("非药化专业 SMILES 多源核查")
    print("对比数据库: PubChem (NIH), NCI CACTUS, ChEMBL (EBI)")
    print("=" * 80)
    
    if not RDKIT_AVAILABLE:
        print("\n⚠️  警告: RDKit 未安装，将使用简化对比模式")
        print("   建议安装 RDKit 以获得更准确的结构对比")
    
    # 加载数据
    if not NON_MED_FILE.exists():
        print(f"错误: 找不到 {NON_MED_FILE}")
        sys.exit(1)
    
    with open(NON_MED_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    print(f"\n共 {len(drugs)} 个药物待核查\n")
    print("-" * 80)
    
    # 统计
    stats = {
        'verified': 0,      # 多源验证通过
        'partial': 0,       # 部分验证
        'mismatch': 0,      # 存在不匹配
        'not_found': 0,     # 未找到参考数据
        'no_smiles': 0      # 无 SMILES
    }
    
    issues_list = []
    all_results = []
    
    for i, drug in enumerate(drugs):
        cn_name = drug.get('cn', '')
        en_name = drug.get('en', '')
        smiles = drug.get('smiles', '')
        
        if not smiles:
            print(f"[{i+1}/{len(drugs)}] ⚠ {cn_name} | {en_name} - 无 SMILES")
            stats['no_smiles'] += 1
            continue
        
        print(f"[{i+1}/{len(drugs)}] 正在核查: {cn_name} | {en_name}...", end="", flush=True)
        
        result = verify_drug(en_name, smiles)
        result['cn_name'] = cn_name
        all_results.append(result)
        
        status = result['status']
        stats[status] = stats.get(status, 0) + 1
        
        if status == 'verified':
            print(f" ✓ 已验证 (多源一致)")
        elif status == 'partial':
            print(f" ○ 部分验证")
        elif status == 'mismatch':
            print(f" ✗ 存在不匹配!")
            issues_list.append(result)
        else:
            print(f" ? 未找到参考数据")
    
    # 生成报告
    print("\n" + "=" * 80)
    print("核查完成！统计结果:")
    print("=" * 80)
    print(f"  ✓ 多源验证通过: {stats['verified']} 个")
    print(f"  ○ 部分验证:     {stats['partial']} 个")
    print(f"  ✗ 存在不匹配:   {stats['mismatch']} 个")
    print(f"  ? 未找到参考:   {stats['not_found']} 个")
    print(f"  ⚠ 无 SMILES:    {stats['no_smiles']} 个")
    
    if issues_list:
        print("\n" + "=" * 80)
        print("⚠️  发现以下药物 SMILES 可能存在问题:")
        print("=" * 80)
        for issue in issues_list:
            print(f"\n【{issue['cn_name']}】{issue['name']}")
            print(f"  当前 SMILES: {issue['current_smiles'][:60]}...")
            if 'current_formula' in issue:
                print(f"  当前分子式: {issue['current_formula']}")
            for problem in issue.get('issues', []):
                print(f"  ❌ {problem}")
            if 'pubchem_smiles' in issue:
                print(f"  📚 PubChem:  {issue['pubchem_smiles'][:60]}...")
            if 'nci_smiles' in issue:
                print(f"  📚 NCI:      {issue['nci_smiles'][:60]}...")
            if 'chembl_smiles' in issue:
                print(f"  📚 ChEMBL:   {issue['chembl_smiles'][:60]}...")
    
    # 保存详细报告
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("非药化专业 SMILES 核查报告\n")
        f.write("=" * 80 + "\n")
        f.write(f"核查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据库: PubChem, NCI CACTUS, ChEMBL\n\n")
        
        f.write("统计结果:\n")
        f.write(f"  多源验证通过: {stats['verified']} 个\n")
        f.write(f"  部分验证: {stats['partial']} 个\n")
        f.write(f"  存在不匹配: {stats['mismatch']} 个\n")
        f.write(f"  未找到参考: {stats['not_found']} 个\n")
        f.write(f"  无 SMILES: {stats['no_smiles']} 个\n\n")
        
        if issues_list:
            f.write("=" * 80 + "\n")
            f.write("问题药物详情:\n")
            f.write("=" * 80 + "\n\n")
            for issue in issues_list:
                f.write(f"【{issue['cn_name']}】{issue['name']}\n")
                f.write(f"  当前 SMILES: {issue['current_smiles']}\n")
                if 'current_formula' in issue:
                    f.write(f"  当前分子式: {issue['current_formula']}\n")
                if 'current_inchi_key' in issue:
                    f.write(f"  当前 InChI Key: {issue['current_inchi_key']}\n")
                for problem in issue.get('issues', []):
                    f.write(f"  问题: {problem}\n")
                if 'pubchem_smiles' in issue:
                    f.write(f"  PubChem SMILES: {issue['pubchem_smiles']}\n")
                if 'nci_smiles' in issue:
                    f.write(f"  NCI SMILES: {issue['nci_smiles']}\n")
                if 'chembl_smiles' in issue:
                    f.write(f"  ChEMBL SMILES: {issue['chembl_smiles']}\n")
                f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("所有验证结果:\n")
        f.write("=" * 80 + "\n\n")
        for r in all_results:
            status_icon = {'verified': '✓', 'partial': '○', 'mismatch': '✗', 'not_found': '?'}.get(r['status'], '-')
            f.write(f"{status_icon} {r['cn_name']} | {r['name']} - {r['status']}\n")
    
    print(f"\n详细报告已保存到: {REPORT_FILE}")
    
    return stats['mismatch']


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
