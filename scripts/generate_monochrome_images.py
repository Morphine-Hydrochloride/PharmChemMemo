#!/usr/bin/env python3
"""
药物分子单色图像生成器 (拟真考试模式)

生成全黑色的分子结构图像，模拟试卷上的印刷效果。
- 所有原子（包括杂原子 O, N, S, Cl 等）都使用黑色
- 为每个分子生成 4 个旋转角度版本 (0°, 90°, 180°, 270°)
- 输出到 /public/assets/images_mono/ 目录
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
DATA_FILE = PROJECT_DIR / "src" / "data.json"
NON_MED_DATA_FILE = PROJECT_DIR / "src" / "non_med_data.json"
VERIFIED_SMILES_FILE = PROJECT_DIR / "src" / "verified_smiles.json"
OUTPUT_DIR = PROJECT_DIR / "public" / "assets" / "images_mono"

# 旋转角度列表
ROTATION_ANGLES = [0, 90, 180, 270]

# -----------------------------------------------------------------------------
# 加载验证过的 SMILES 数据库
# -----------------------------------------------------------------------------
if VERIFIED_SMILES_FILE.exists():
    with open(VERIFIED_SMILES_FILE, 'r', encoding='utf-8') as f:
        LOCAL_SMILES_DB = json.load(f)
    print(f"已加载 {len(LOCAL_SMILES_DB)} 个经过验证的 SMILES 数据")
else:
    print("警告: 找不到 verified_smiles.json")
    LOCAL_SMILES_DB = {}

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


def process_data_file(data_file):
    """处理单个数据文件"""
    if not data_file.exists():
        print(f"找不到数据文件: {data_file}")
        return 0
    
    with open(data_file, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    count = 0
    
    for i, drug in enumerate(drugs):
        en_name = drug.get("en", "").strip()
        cn_name = drug.get("cn", "")
        drug_id = drug.get("id", "").replace("fam-", "").replace("mas-", "")
        
        if not drug_id: 
            continue

        smiles = ""
        
        if en_name in LOCAL_SMILES_DB:
            smiles = LOCAL_SMILES_DB[en_name]
        else:
             base_name = en_name.replace(" hydrochloride", "").replace(" hydrobromide", "").replace(" sodium", "")
             if base_name in LOCAL_SMILES_DB:
                 smiles = LOCAL_SMILES_DB[base_name]

        if not smiles:
             smiles = drug.get("smiles", "")
        
        if not smiles:
            print(f"[{i+1}] 跳过 (无数据): {cn_name} | {en_name}")
            continue
            
        parent_smiles = extract_parent_molecule(smiles)
        
        # 为每个旋转角度生成图像
        for angle in ROTATION_ANGLES:
            if angle == 0:
                output_filename = f"{drug_id}.svg"
            else:
                output_filename = f"{drug_id}_r{angle}.svg"
            
            output_path = OUTPUT_DIR / output_filename
            
            if render_molecule_svg_monochrome(parent_smiles, output_path, rotation=angle):
                if angle == 0:
                    print(f"[{i+1}] 生成: {cn_name} (4个角度)")
                count += 1
            else:
                print(f"   -> 失败! ({angle}°)")
    
    return count


def main():
    print("=" * 60)
    print("药物分子单色图像生成器 (拟真考试模式)")
    print("每个分子生成 4 个旋转角度版本")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_count = 0
    
    # 处理药化专业数据
    print("\n--- 处理药化专业数据 ---")
    total_count += process_data_file(DATA_FILE)
    
    # 处理非药化专业数据
    print("\n--- 处理非药化专业数据 ---")
    total_count += process_data_file(NON_MED_DATA_FILE)
    
    print(f"\n{'=' * 60}")
    print(f"完成！共生成 {total_count} 个单色分子图像")
    print(f"(每个分子 4 个角度)")
    print(f"输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
