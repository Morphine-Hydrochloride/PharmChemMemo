import os
import re
import json

PPT_CONTENT_DIR = "ppt_content"
OUTPUT_FILE = "src/keyPointsData_generated.js"

# Maps for standardized keys
KEY_MAPPING = {
    "结构": "【结构】",
    "理化性质": "【性质】",
    "化学不稳定性": "【性质】",
    "不稳定性": "【性质】",
    "体内代谢": "【代谢】",
    "代谢/稳定性": "【代谢】",
    "临床用途": "【临床】",
    "临床应用": "【临床】",
    "合成方法": "【合成】",
    "合成路线": "【合成】",
    "作用机制": "【机制】",
    "作用机理": "【机制】",
    "药效特点": "【特点】",
    "相关考点": "【考点】",
    "不稳定性等": "【性质】",
    "代谢": "【代谢】",
    "用途": "【临床】",
    "副作用": "【副作用】",
    "构效关系": "【SAR】",
}

def parse_markdown_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    drugs = {}
    current_category = "familiar" # default
    current_drug = None
    
    # Check for category sections
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect Category
        if "掌握" in line and ("###" in line or "1." in line):
            current_category = "master"
        elif "熟悉" in line and ("###" in line or "1." in line or "2." in line):
            current_category = "familiar"
            


        # Detect Knowledge Points (Bullet points)
        # Must strictly start with "* " or "- " to avoid catching "**Bold**" headers
        if line.startswith('* ') or line.startswith('- '):
            if current_drug:
                # Remove bullet point
                point_content = line.lstrip('*- ').strip()
                if not point_content: 
                    continue
                    
                # Split by colon if present to identify type
                if "：" in point_content or ":" in point_content:
                    parts = re.split(r'[:：]', point_content, 1)
                    key_raw = parts[0].strip().replace("**", "")
                    val = parts[1].strip()
                    
                    # clean key
                    std_key = "【其他】"
                    for k, v in KEY_MAPPING.items():
                        if k in key_raw:
                            std_key = v
                            break
                    
                    # Check for 【掌握】 prefix
                    prefix = "【掌握】" if drugs[current_drug]["category"] == "master" else ""
                    
                    final_str = f"{prefix}{std_key}{val}"
                    drugs[current_drug]["points"].append(final_str)
                else:
                     # No key, just valid content
                     prefix = "【掌握】" if drugs[current_drug]["category"] == "master" else ""
                     drugs[current_drug]["points"].append(f"{prefix}{point_content}")
            continue
            
        # Detect Drug Name (Only if NOT a bullet point)
        # Pattern 1: **中文名 (English Name)**
        # Pattern 2: #### 1. 中文名 (English Name)
        # We look for the (...) part.
        drug_match = re.search(r'(?:\*\*|####\s*\d+\.\s*)(?:.*?)[\(（](.*?)[\)）]', line)
        if drug_match:
            raw_en_name = drug_match.group(1).split('/')[0].strip() # Take first name if "Name/Alias"
            
            # Basic validation: If the name is too long or contains Chinese, it's probably not an English Name
            # (PPT sometimes has (例如...) or (see page...))
            if len(raw_en_name) > 50 or re.search(r'[\u4e00-\u9fff]', raw_en_name):
                continue
                
            # specific cleanup
            if " Hydrochloride" in raw_en_name:
                raw_en_name = raw_en_name.replace(" Hydrochloride", "")
            if " hydrochloride" in raw_en_name:
                raw_en_name = raw_en_name.replace(" hydrochloride", "")
            if " Sulfate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" Sulfate", "")
            if " sulfate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" sulfate", "")
            if " Nitrate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" Nitrate", "")
            if " nitrate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" nitrate", "")
            if " Citrate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" Citrate", "") 
            if " citrate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" citrate", "")
            if " Maleate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" Maleate", "")
            if " maleate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" maleate", "")
            if " Tartrate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" Tartrate", "")
            if " tartrate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" tartrate", "")
            if " Sodium" in raw_en_name:
                raw_en_name = raw_en_name.replace(" Sodium", "")
            if " sodium" in raw_en_name:
                raw_en_name = raw_en_name.replace(" sodium", "")
            if " Acetate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" Acetate", "")
            if " acetate" in raw_en_name:
                raw_en_name = raw_en_name.replace(" acetate", "")
            if " HCl" in raw_en_name:
                raw_en_name = raw_en_name.replace(" HCl", "")
            
            # Clean up parenthesis inside name if any
            raw_en_name = re.sub(r'\s*\(.*?\)', '', raw_en_name)
            
            current_drug = raw_en_name.strip()
            # Standardize capitalization
            current_drug = current_drug[0].upper() + current_drug[1:]
            
            drugs[current_drug] = {
                "category": current_category,
                "points": []
            }
            continue

    return drugs

def main():
    all_drugs = {}
    
    # List files numeric sort
    files = [f for f in os.listdir(PPT_CONTENT_DIR) if f.endswith('.md')]
    # simple sort by number
    files.sort(key=lambda x: int(x.split('.')[0]))

    for filename in files:
        filepath = os.path.join(PPT_CONTENT_DIR, filename)
        print(f"Processing {filename}...")
        parsed = parse_markdown_file(filepath)
        all_drugs.update(parsed)

    # Generate JS content
    output_lines = []
    output_lines.append("// --- 药物考点全量数据库 ---")
    output_lines.append("// 包含了结构特征、理化性质、代谢、合成重点等")
    output_lines.append("// 此文件由脚本 scripts/update_keypoints.py 自动生成，请勿手动修改（除非必要）")
    output_lines.append("export const KEY_POINTS_DB = {")
    
    for drug_name, data in all_drugs.items():
        points = data["points"]
        if not points:
            continue
            
        # Format as JS array
        points_js = json.dumps(points, ensure_ascii=False)
        output_lines.append(f'    "{drug_name}": {points_js},')

    output_lines.append("};")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
        
    print(f"Successfully generated {OUTPUT_FILE} with {len(all_drugs)} drugs.")

if __name__ == "__main__":
    main()
