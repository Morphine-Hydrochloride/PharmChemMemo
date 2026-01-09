#!/usr/bin/env python3
"""
药物分子教科书风格图像生成器 (NCI 验证版)

使用 RDKit 从 SMILES 生成专业的化学结构图像。
- 数据源: verified_smiles.json (来自 NCI CACTUS 验证)
- 自动移除盐酸、枸橼酸、磷酸等成盐部分，只渲染药物母核
- 生成高质量 SVG 图像
"""

import json
import os
import sys
import time
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import Draw, AllChem, rdDepictor
    from rdkit.Chem.Draw import rdMolDraw2D
except ImportError:
    print("错误: 请先安装 RDKit")
    print("运行: pip install rdkit")
    sys.exit(1)

# 路径配置
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_FILE = PROJECT_DIR / "src" / "data.json"
VERIFIED_SMILES_FILE = PROJECT_DIR / "src" / "verified_smiles.json"
OUTPUT_DIR = PROJECT_DIR / "public" / "assets" / "images"

# -----------------------------------------------------------------------------
# 加载验证过的 SMILES 数据库
# -----------------------------------------------------------------------------
if VERIFIED_SMILES_FILE.exists():
    with open(VERIFIED_SMILES_FILE, 'r', encoding='utf-8') as f:
        LOCAL_SMILES_DB = json.load(f)
    print(f"已加载 {len(LOCAL_SMILES_DB)} 个经过验证的 SMILES 数据")
else:
    print("警告: 找不到 verified_smiles.json，请先运行 sync_from_nci.py")
    LOCAL_SMILES_DB = {}

# -----------------------------------------------------------------------------

def extract_parent_molecule(smiles, keep_sodium=False):
    """
    从复合 SMILES 中提取药物母核（最大片段），去除盐/酸
    keep_sodium: 如果为 True，则不去除钠离子
    """
    if not smiles:
        return None
    
    # 清理: 有些 SMILES 可能包含多余的转义符 (来自 JSON)
    smiles = smiles.replace("\\", "")

    # 分割多组分 SMILES（用 . 分隔）
    fragments = smiles.split(".")
    
    if len(fragments) == 1:
        return smiles
    
    # 找出最大的非盐片段
    best_fragment = None
    best_size = 0
    
    # Define salt/ion list
    base_salts = ["Cl", "[Cl-]", "Br", "[Br-]", "[I-]", "[K+]", "[K]", "[Li+]", "[Ca+2]", "[Mg+2]", "[H+]"]
    
    # 【修复】对于铂类药物 (Pt)，如顺铂，必须保留所有配体 (Cl, NH3 等)，不能拆分
    if "Pt" in smiles or "[Pt" in smiles or "pt" in smiles.lower():
        return smiles

    if not keep_sodium:
        base_salts.extend(["[Na+]", "[Na]"])
    
    # First pass: try to find a clear "parent" that isn't a salt/acid
    for frag in fragments:
        is_salt = False
        
        # 1. Simple metal ions/halogens - Always exclude
        if frag in base_salts:
            is_salt = True
        
        # 2. Check molecular properties
        if not is_salt:
            mol = Chem.MolFromSmiles(frag)
            if mol:
                num_heavy = mol.GetNumHeavyAtoms()
                
                # Very small molecules might be solvents/salts
                if num_heavy <= 3:
                    is_salt = True
                
                # Heuristic for organic acids as counterions (e.g. Fumaric, Maleic, etc.)
                # Rule: Small (<12 heavy) AND only composed of {C,O,H,P,S}
                # ISSUE FIX: Some drugs (like Valproate) also fit this!
                # So we only mark them as potential salts, but we keep track of them.
                elif num_heavy <= 12:
                    atoms = [atom.GetSymbol() for atom in mol.GetAtoms()]
                    if set(atoms).issubset({'C', 'O', 'H', 'P', 'S'}):
                        is_salt = True # Mark as "likely salt/acid" for now
                
                # If it passed all "is_salt" checks, it's a strong candidate for the parent
                if not is_salt:
                     if num_heavy > best_size:
                        best_size = num_heavy
                        best_fragment = frag

    # Logic:
    # 1. If we found a "best_fragment" that is explicitly NOT a salt, return it.
    if best_fragment:
        # If keeping sodium, and we found a parent, we should try to return the full set if possible?
        # Actually, for salts like "Phenytoin Sodium", SMILES is "[Na+].[Anion-]".
        # If we just return `[Na+].[Anion-]` it works?
        # But `extract_parent_molecule` is usually "return ONE fragment".
        # If keep_sodium is True, we generally want to return the whole thing IF it looks like a sodium salt.
        # But wait, `render_molecule_svg` takes a SMILES string. RDKit draws multiple fragments if passed "A.B".
        
        if keep_sodium:
             # Check if original SMILES contains Na+ and we want to keep it
             if "[Na+]" in smiles or "[Na]" in smiles:
                 return smiles # Return the FULL original SMILES (cleaned)

        return best_fragment
    
    # 2. Fallback: If ALL fragments looked like salts (e.g. Sodium Valproate -> [Na+] and Valproate ion),
    # we pick the LARGEST fragment that is NOT a simple inorganic ion.
    
    candidates = []
    for frag in fragments:
        # Exclude inorganic ions again
        if frag in base_salts:
            continue
            
        mol = Chem.MolFromSmiles(frag)
        if mol:
            candidates.append((frag, mol.GetNumHeavyAtoms()))
    
    if candidates:
        # Sort by size (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        # Check keep_sodium fallback
        if keep_sodium and ("[Na+]" in smiles or "[Na]" in smiles):
            return smiles
        return candidates[0][0]

    # 3. Last resort: just return the first one (likely the string was just ions?)
    return fragments[0]


def render_molecule_svg(smiles, output_path, width=400, height=400):
    """
    使用 RDKit 渲染教科书风格的分子 SVG
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        # 清除现有构象并重新生成 2D 坐标（确保整洁）
        AllChem.Compute2DCoords(mol)
        
        # 创建绘图器
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        
        # 优先使用 CoordGen (Schrodinger) 算法，这对大环（如红霉素）的圆形布局支持更好
        if hasattr(rdDepictor, 'SetPreferCoordGen'):
            rdDepictor.SetPreferCoordGen(True)

        # 教科书风格选项
        opts = drawer.drawOptions()
        opts.bondLineWidth = 2.5           # 加粗键线
        opts.minFontSize = 16              # 增大字体
        opts.maxFontSize = 24
        opts.additionalAtomLabelPadding = 0.15
        opts.addStereoAnnotation = True    # 必须显示立体化学 (R/S, E/Z, 楔形键)
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
            11: (0.5, 0.0, 0.5)   # Na: Purple/Dark (add specifically if visible)
        }
        
        # 应用颜色 (使用 setAtomPalette 确保生效)
        opts.setAtomPalette(atom_colors)

        # 绘制
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        
        # 保存
        svg_text = drawer.GetDrawingText()
        svg_path = output_path.with_suffix('.svg')
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_text)
            
        return True
    except Exception as e:
        print(f"渲染错误 {output_path.name}: {e}")
        return False


def main():
    print("=" * 60)
    print("药物分子图像生成器 (NCI 验证版)")
    print("=" * 60)
    
    if not DATA_FILE.exists():
        print(f"找不到数据文件: {DATA_FILE}")
        return
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    count = 0
    updated_count = 0
    
    for i, drug in enumerate(drugs):
        en_name = drug.get("en", "").strip()
        cn_name = drug.get("cn", "")
        drug_id = drug.get("id", "").replace("fam-", "").replace("mas-", "")
        
        if not drug_id: continue

        smiles = ""
        
        # 0. 【新增】优先使用 data.json 中的 InChI (最可靠来源)
        inchi = drug.get("inchi", "")
        if inchi:
            try:
                from rdkit.Chem.inchi import MolFromInchi
                mol_from_inchi = MolFromInchi(inchi)
                if mol_from_inchi:
                    # 尝试规范化互变异构体（恢复酮式结构，解决 Enol 问题）
                    try:
                        from rdkit.Chem.MolStandardize import rdMolStandardize
                        enumerator = rdMolStandardize.TautomerEnumerator()
                        mol_from_inchi = enumerator.Canonicalize(mol_from_inchi)
                    except Exception as te:
                        print(f"Tautomer canonicalization failed for {en_name}: {te}")

                    smiles = Chem.MolToSmiles(mol_from_inchi)
                    # print(f"Using InChI for {en_name}") 
            except Exception as e:
                print(f"Warning: Failed to parse InChI for {en_name}: {e}")

        # 1. 如果没有 InChI，则从 verified_smiles.json 中查找
        if not smiles:
            # 匹配全名
            if en_name in LOCAL_SMILES_DB:
                smiles = LOCAL_SMILES_DB[en_name]
            # 匹配去盐后的名称 (如果 verified database 用的是 base name)
            else:
                 base_name = en_name.replace(" hydrochloride", "").replace(" hydrobromide", "").replace(" sodium", "")
                 if base_name in LOCAL_SMILES_DB:
                     smiles = LOCAL_SMILES_DB[base_name]

        # 2. 如果 verified db 没找到，才用 data.json 中原有的 (作为 fallback)
        if not smiles:
             smiles = drug.get("smiles", "")
        
        if not smiles:
            print(f"[{i+1}] 跳过 (无数据): {cn_name} | {en_name}")
            continue
            
        # 3. 提取母核 (去除盐)
        # 特殊逻辑：如果是钠盐且药名含“钠”，则保留钠离子
        is_sodium_salt = "sodium" in en_name.lower() or "钠" in cn_name
        parent_smiles = extract_parent_molecule(smiles, keep_sodium=is_sodium_salt)
        
        # 4. 生成 SVG
        output_filename = f"{drug_id}.svg"
        output_path = OUTPUT_DIR / output_filename
        
        print(f"[{i+1}] 生成: {cn_name} -> {str(parent_smiles)[:30]}...")
        if render_molecule_svg(parent_smiles, output_path):
            drug["image"] = f"/assets/images/{output_filename}"
            drug["smiles"] = smiles # 确保 data.json 也保存了最新的 SMILES
            count += 1
            updated_count += 1
        else:
            print(f"   -> 失败!")

    # 保存结果
    if updated_count > 0:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(drugs, f, ensure_ascii=False, indent=2)
        print(f"\n成功更新了 {updated_count} 个药物的图像和数据！")
    else:
        print("\n没有更变。")

if __name__ == "__main__":
    main()
