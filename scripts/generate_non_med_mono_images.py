#!/usr/bin/env python3
"""
非药化专业 - 单色分子图像生成器 (拟真考试模式)

为非药化专业生成全黑色的分子结构图像，模拟试卷上的印刷效果。
- 所有原子（包括杂原子 O, N, S, Cl 等）都使用黑色
- 为每个分子生成 4 个旋转角度版本 (0°, 90°, 180°, 270°)
- 输出到 /public/assets/images_non_med_mono/ 目录
- 文件名格式与 images_non_med 保持一致，如 fam-Ch7-Famotidine.svg
"""

import json
import math
import sys
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, rdDepictor
    from rdkit.Chem.Draw import rdMolDraw2D
    from rdkit.Geometry import Point3D
except ImportError:
    print("错误: 请先安装 RDKit")
    print("运行: pip install rdkit")
    sys.exit(1)

# 路径配置
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NON_MED_DATA_FILE = PROJECT_DIR / "src" / "非药化专业.json"
OUTPUT_DIR = PROJECT_DIR / "public" / "assets" / "images_non_med_mono"

# 旋转角度列表
ROTATION_ANGLES = [0, 90, 180, 270]

# -----------------------------------------------------------------------------

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
        
        if frag in ["Cl", "[Cl-]", "Br", "[Br-]", "[I-]", "[Na+]", "[K+]", "[Na]", "[K]", "[Li+]", "[Ca+2]", "[Mg+2]", "[H+]"]:
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
        if frag in ["Cl", "[Cl-]", "Br", "[Br-]", "[I-]", "[Na+]", "[K+]", "[Na]", "[K]", "[Li+]", "[Ca+2]", "[Mg+2]", "[H+]"]:
            continue
            
        mol = Chem.MolFromSmiles(frag)
        if mol:
            candidates.append((frag, mol.GetNumHeavyAtoms()))
    
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    return fragments[0]


def rotate_mol_2d(mol, angle_degrees):
    """
    旋转分子的2D坐标
    angle_degrees: 旋转角度（度数）
    """
    if mol.GetNumConformers() == 0:
        AllChem.Compute2DCoords(mol)
    
    conf = mol.GetConformer()
    angle_rad = math.radians(angle_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # 计算中心点
    center_x = sum(conf.GetAtomPosition(i).x for i in range(mol.GetNumAtoms())) / mol.GetNumAtoms()
    center_y = sum(conf.GetAtomPosition(i).y for i in range(mol.GetNumAtoms())) / mol.GetNumAtoms()
    
    # 旋转每个原子坐标
    for i in range(mol.GetNumAtoms()):
        pos = conf.GetAtomPosition(i)
        # 相对于中心的坐标
        dx = pos.x - center_x
        dy = pos.y - center_y
        # 旋转
        new_x = dx * cos_a - dy * sin_a + center_x
        new_y = dx * sin_a + dy * cos_a + center_y
        conf.SetAtomPosition(i, Point3D(new_x, new_y, 0))
    
    return mol


def render_molecule_svg_monochrome(smiles, output_path, width=400, height=400, rotation=0):
    """
    渲染单色（全黑）分子 SVG - 模拟试卷印刷效果
    rotation: 旋转角度（0, 90, 180, 270）
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        AllChem.Compute2DCoords(mol)
        
        # 应用旋转
        if rotation != 0:
            mol = rotate_mol_2d(mol, rotation)
        
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        
        if hasattr(rdDepictor, 'SetPreferCoordGen'):
            rdDepictor.SetPreferCoordGen(True)

        opts = drawer.drawOptions()
        opts.bondLineWidth = 2.5
        opts.minFontSize = 16
        opts.maxFontSize = 24
        opts.additionalAtomLabelPadding = 0.15
        opts.addStereoAnnotation = True
        opts.addAtomIndices = False
        opts.padding = 0.05
        
        # 所有原子都使用黑色
        BLACK = (0, 0, 0)
        atom_colors = {
            6: BLACK, 8: BLACK, 7: BLACK, 17: BLACK,
            16: BLACK, 9: BLACK, 15: BLACK, 35: BLACK, 53: BLACK,
        }
        opts.setAtomPalette(atom_colors)

        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        
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
    print("非药化专业 - 单色图像生成器 (拟真考试模式)")
    print("每个分子生成 4 个旋转角度版本")
    print("=" * 60)
    
    # 检查数据文件
    if not NON_MED_DATA_FILE.exists():
        print(f"错误: 找不到数据文件: {NON_MED_DATA_FILE}")
        sys.exit(1)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载非药化专业数据
    with open(NON_MED_DATA_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    print(f"\n共 {len(drugs)} 个药物")
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for i, drug in enumerate(drugs):
        cn_name = drug.get("cn", "")
        en_name = drug.get("en", "")
        drug_id = drug.get("id", "")  # 如 fam-Ch7-Famotidine
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
        
        # 为每个旋转角度生成图像
        all_success = True
        for angle in ROTATION_ANGLES:
            if angle == 0:
                output_filename = f"{drug_id}.svg"
            else:
                output_filename = f"{drug_id}_r{angle}.svg"
            
            output_path = OUTPUT_DIR / output_filename
            
            if not render_molecule_svg_monochrome(parent_smiles, output_path, rotation=angle):
                all_success = False
                print(f"   -> 失败! ({angle}°)")
        
        if all_success:
            print(f"[{i+1}/{len(drugs)}] ✓ 生成: {cn_name} (4个角度)")
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"完成！")
    print(f"  成功: {success_count} 个药物 ({success_count * 4} 个图像)")
    print(f"  失败: {fail_count} 个药物")
    print(f"  跳过: {skip_count} 个药物")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
