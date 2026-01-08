#!/usr/bin/env python3
"""
非药化专业 - 彩色分子图像生成器

使用 RDKit 从 SMILES 生成专业的化学结构图像。
- 数据源: 非药化专业.json (已修复的 SMILES)
- 生成高质量彩色 SVG 图像
- 输出到 /public/assets/images_non_med/ 目录
"""

import json
import sys
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, rdDepictor
    from rdkit.Chem.Draw import rdMolDraw2D
except ImportError:
    print("错误: 请先安装 RDKit")
    print("运行: pip install rdkit")
    sys.exit(1)

# 路径配置
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NON_MED_DATA_FILE = PROJECT_DIR / "src" / "非药化专业.json"
OUTPUT_DIR = PROJECT_DIR / "public" / "assets" / "images_non_med"


def extract_parent_molecule(smiles):
    """从复合 SMILES 中提取药物母核（最大片段），去除盐/酸"""
    if not smiles:
        return None
    
    smiles = smiles.replace("\\", "")
    fragments = smiles.split(".")
    
    if len(fragments) == 1:
        return smiles
    
    best_fragment = None
    best_size = 0
    
    for frag in fragments:
        is_salt = False
        
        if frag in ["Cl", "[Cl-]", "Br", "[Br-]", "[I-]", "[Na+]", "[K+]", "[Na]", "[K]", "[Li+]", "[Ca+2]", "[Mg+2]", "[H+]", "O", "[OH-]"]:
            is_salt = True
        
        if not is_salt:
            mol = Chem.MolFromSmiles(frag)
            if mol:
                num_heavy = mol.GetNumHeavyAtoms()
                
                if num_heavy <= 3:
                    is_salt = True
                elif num_heavy <= 12:
                    atoms = [atom.GetSymbol() for atom in mol.GetAtoms()]
                    if set(atoms).issubset({'C', 'O', 'H', 'P', 'S'}):
                        is_salt = True
                
                if not is_salt:
                     if num_heavy > best_size:
                        best_size = num_heavy
                        best_fragment = frag

    if best_fragment:
        return best_fragment
    
    candidates = []
    for frag in fragments:
        if frag in ["Cl", "[Cl-]", "Br", "[Br-]", "[I-]", "[Na+]", "[K+]", "[Na]", "[K]", "[Li+]", "[Ca+2]", "[Mg+2]", "[H+]", "O", "[OH-]"]:
            continue
            
        mol = Chem.MolFromSmiles(frag)
        if mol:
            candidates.append((frag, mol.GetNumHeavyAtoms()))
    
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    return fragments[0]


def render_molecule_svg(smiles, output_path, width=400, height=400):
    """使用 RDKit 渲染教科书风格的分子 SVG"""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        # 清除现有构象并重新生成 2D 坐标
        AllChem.Compute2DCoords(mol)
        
        # 创建绘图器
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        
        # 优先使用 CoordGen 算法
        if hasattr(rdDepictor, 'SetPreferCoordGen'):
            rdDepictor.SetPreferCoordGen(True)

        # 教科书风格选项
        opts = drawer.drawOptions()
        opts.bondLineWidth = 2.5
        opts.minFontSize = 16
        opts.maxFontSize = 24
        opts.additionalAtomLabelPadding = 0.15
        opts.addStereoAnnotation = True
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
            35: (0.6, 0.1, 0.1),  # Br: 深红色
            53: (0.5, 0.0, 0.5),  # I: 紫色
        }
        
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
    print("=" * 70)
    print("非药化专业 - 彩色分子图像生成器")
    print("=" * 70)
    
    if not NON_MED_DATA_FILE.exists():
        print(f"错误: 找不到数据文件: {NON_MED_DATA_FILE}")
        sys.exit(1)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    with open(NON_MED_DATA_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    print(f"\n共 {len(drugs)} 个药物")
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for i, drug in enumerate(drugs):
        cn_name = drug.get("cn", "")
        en_name = drug.get("en", "")
        drug_id = drug.get("id", "")
        smiles = drug.get("smiles", "")
        
        if not drug_id:
            print(f"[{i+1}] 跳过 (无ID): {cn_name}")
            skip_count += 1
            continue
        
        if not smiles:
            print(f"[{i+1}] 跳过 (无SMILES): {cn_name} | {en_name}")
            skip_count += 1
            continue
        
        parent_smiles = extract_parent_molecule(smiles)
        
        if not parent_smiles:
            print(f"[{i+1}] 跳过 (SMILES解析失败): {cn_name}")
            skip_count += 1
            continue
        
        output_filename = f"{drug_id}.svg"
        output_path = OUTPUT_DIR / output_filename
        
        if render_molecule_svg(parent_smiles, output_path):
            print(f"[{i+1}/{len(drugs)}] ✓ {cn_name} ({en_name})")
            success_count += 1
            
            # 更新 drug 中的 image 路径
            drug["image"] = f"/assets/images_non_med/{output_filename}"
        else:
            print(f"[{i+1}/{len(drugs)}] ✗ 失败: {cn_name}")
            fail_count += 1
    
    # 保存更新后的数据（包含正确的 image 路径）
    with open(NON_MED_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 70}")
    print(f"完成！")
    print(f"  成功: {success_count} 个")
    print(f"  失败: {fail_count} 个")
    print(f"  跳过: {skip_count} 个")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"\n数据已更新到 {NON_MED_DATA_FILE}")


if __name__ == "__main__":
    main()
