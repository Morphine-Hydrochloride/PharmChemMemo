#!/usr/bin/env python3
"""
从PubChem下载所有药物的InChI，存储到data.json，并使用InChI重新生成分子图像
InChI是标准化的分子标识符，比SMILES更可靠
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
    from rdkit.Chem import Draw, AllChem
    from rdkit.Chem.Draw import rdMolDraw2D
    from rdkit.Chem.inchi import MolFromInchi
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
    print("错误: 需要安装RDKit才能运行此脚本")
    print("请运行: pip install rdkit")
    exit(1)

# 路径配置
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR.parent / 'src' / 'data.json'
INCHI_CACHE_FILE = SCRIPT_DIR.parent / 'src' / 'inchi_cache.json'
OUTPUT_DIR = SCRIPT_DIR.parent / 'public' / 'assets' / 'images'

def get_pubchem_inchi(drug_name_en):
    """通过英文名从PubChem获取InChI"""
    # 清理药物名称 - 去掉盐形式后缀
    clean_name = drug_name_en
    for suffix in [" hydrochloride", " maleate", " sulfate", " sodium", " tartrate", 
                   " phosphate", " besilate", " citrate", " bromide", " nitrate", 
                   " oxalate", " mesylate", " dihydrochloride", " hydrobromide"]:
        clean_name = clean_name.replace(suffix, "")
    clean_name = clean_name.strip()
    
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(clean_name)}/property/InChI,MolecularFormula/JSON"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            props = data['PropertyTable']['Properties'][0]
            return {
                'inchi': props.get('InChI', ''),
                'formula': props.get('MolecularFormula', ''),
                'cid': props.get('CID', '')
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'error': 'Not found'}
        return {'error': f'HTTP {e.code}'}
    except Exception as e:
        return {'error': str(e)[:100]}

def render_molecule_from_inchi(inchi, output_path, width=400, height=400):
    """使用RDKit从InChI渲染教科书风格的分子SVG"""
    try:
        from rdkit.Chem import rdDepictor
        
        mol = MolFromInchi(inchi)
        if mol is None:
            return False
        
        # 优先使用 CoordGen (Schrodinger) 算法，对大环分子布局更好
        if hasattr(rdDepictor, 'SetPreferCoordGen'):
            rdDepictor.SetPreferCoordGen(True)
        
        # 添加2D坐标
        AllChem.Compute2DCoords(mol)
        
        # 创建SVG绘图器
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        
        # 教科书风格选项
        opts = drawer.drawOptions()
        opts.bondLineWidth = 2.5           # 加粗键线
        opts.minFontSize = 16              # 增大字体
        opts.maxFontSize = 24
        opts.additionalAtomLabelPadding = 0.15
        opts.addStereoAnnotation = True    # 显示立体化学 (R/S, E/Z, 楔形键)
        opts.addAtomIndices = False
        opts.padding = 0.05
        
        # 自定义原子颜色 (教科书风格)
        atom_colors = {
            8: (0.9, 0.1, 0.1),   # O: 红色
            7: (0.1, 0.1, 0.9),   # N: 蓝色
            17: (0.1, 0.8, 0.1),  # Cl: 浅绿色
            16: (0.9, 0.6, 0.1),  # S: 橙色
            9: (0.2, 0.9, 0.4),   # F: 亮绿色
            15: (0.6, 0.1, 0.8),  # P: 紫色
            35: (0.6, 0.3, 0.1),  # Br: 棕色
            53: (0.5, 0.0, 0.5),  # I: 深紫色
            11: (0.5, 0.0, 0.5)   # Na: 深紫色
        }
        
        # 应用颜色
        opts.setAtomPalette(atom_colors)
        
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        
        svg_content = drawer.GetDrawingText()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        return True
    except Exception as e:
        print(f"渲染失败: {e}")
        return False

def main():
    print("=" * 60)
    print("从PubChem下载InChI并重新生成分子图像")
    print("=" * 60)
    
    # 加载数据
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    # 加载InChI缓存（如果存在）
    inchi_cache = {}
    if INCHI_CACHE_FILE.exists():
        with open(INCHI_CACHE_FILE, 'r', encoding='utf-8') as f:
            inchi_cache = json.load(f)
        print(f"已加载 {len(inchi_cache)} 个缓存的InChI")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"开始处理 {len(drugs)} 种药物...\n")
    
    success_count = 0
    failed_list = []
    
    for i, drug in enumerate(drugs):
        cn = drug['cn']
        en = drug['en']
        drug_id = drug.get('id', '').replace('fam-', '').replace('mas-', '')
        
        if not drug_id:
            continue
        
        print(f"[{i+1}/{len(drugs)}] {cn} ({en})...", end=' ', flush=True)
        
        # 1. 检查缓存
        if en in inchi_cache:
            inchi = inchi_cache[en]
            source = "缓存"
        else:
            # 2. 从PubChem获取
            pubchem_data = get_pubchem_inchi(en)
            
            if 'error' in pubchem_data:
                print(f"✗ {pubchem_data['error']}")
                failed_list.append({'drug': cn, 'en': en, 'error': pubchem_data['error']})
                continue
            
            inchi = pubchem_data['inchi']
            inchi_cache[en] = inchi  # 保存到缓存
            source = "PubChem"
        
        # 3. 验证InChI可以被解析
        mol = MolFromInchi(inchi)
        if mol is None:
            print(f"✗ InChI无效")
            failed_list.append({'drug': cn, 'en': en, 'error': 'Invalid InChI'})
            continue
        
        # 4. 更新药物数据 - 存储InChI
        drug['inchi'] = inchi
        
        # 5. 生成图像
        output_path = OUTPUT_DIR / f"{drug_id}.svg"
        
        if render_molecule_from_inchi(inchi, output_path):
            drug['image'] = f"/assets/images/{drug_id}.svg"
            print(f"✓ 成功 ({source})")
            success_count += 1
        else:
            print(f"✗ 渲染失败")
            failed_list.append({'drug': cn, 'en': en, 'error': 'Render failed'})
        
        time.sleep(0.2)  # 避免请求过快
    
    # 保存更新后的data.json
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=2)
    
    # 保存InChI缓存
    with open(INCHI_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(inchi_cache, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"成功: {success_count} 个")
    print(f"失败: {len(failed_list)} 个")
    print(f"InChI缓存已保存到: {INCHI_CACHE_FILE}")
    
    if failed_list:
        print("\n失败列表:")
        for item in failed_list:
            print(f"  - {item['drug']} ({item['en']}): {item['error']}")
        
        # 保存失败列表
        failed_path = SCRIPT_DIR.parent / 'inchi_failed.json'
        with open(failed_path, 'w', encoding='utf-8') as f:
            json.dump(failed_list, f, ensure_ascii=False, indent=2)
        print(f"\n失败列表已保存到: {failed_path}")

if __name__ == '__main__':
    main()
