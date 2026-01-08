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

def parse_markdown_file(filepath, cn_map, en_map):
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
            
        # Pattern 1: **中文名 (English Name)**
        # Pattern 2: #### 1. 中文名 (English Name)
        drug_match = re.search(r'(?:\*\*|####\s*\d+\.\s*)(?:.*?)([\u4e00-\u9fa5]+).*?[\(（](.*?)[\)）]', line)
        
        canonical_name = None
        
        if drug_match:
            raw_cn_name = drug_match.group(1).strip()
            raw_en_name = drug_match.group(2).split('/')[0].strip() # Take first name if "Name/Alias"

            # 1. Try match by Chinese Name (Highest Priority)
            if raw_cn_name in cn_map:
                canonical_name = cn_map[raw_cn_name]
            else:
                # 2. Try match by English Name (exact or cleaned)
                
                # specific cleanup for matching attempts
                clean_en_name = raw_en_name
                
                # Common suffix removal for matching attempt
                suffixes = [" Hydrochloride", " hydrochloride", " Sulfate", " sulfate", " Nitrate", " nitrate", 
                           " Citrate", " citrate", " Maleate", " maleate", " Tartrate", " tartrate", 
                           " Sodium", " sodium", " Acetate", " acetate", " HCl", " Besylate", " besylate"]
                
                for s in suffixes:
                    clean_en_name = clean_en_name.replace(s, "")
                
                clean_en_name = re.sub(r'\s*\(.*?\)', '', clean_en_name).strip()
                
                # Check mapping
                if raw_en_name.lower() in en_map:
                    canonical_name = en_map[raw_en_name.lower()]
                elif clean_en_name.lower() in en_map: 
                     # This creates a risk: if we map "Risedronate" to "Risedronate sodium", that's good.
                     # But we must be sure.
                     # Let's check if the clean name exists as a key in en_map (which are lowercased official names)
                     # Actually en_map keys are lower cased official names.
                     # So if data.json has "Risedronate sodium", en_map has "risedronate sodium".
                     # "Risedronate" won't match "risedronate sodium".
                     
                     # We need to do a reverse partial match or just trust the clean name if no match found?
                     # No, if we want to fix "Risedronate" -> "Risedronate sodium", we rely on the Chinese name match primarily.
                     
                     # If Chinese name fails, we fall back to:
                     pass

            # If still no canonical name found, we use the cleaned English Name as fallback (current behavior)
            if not canonical_name:
                 # Standard cleanup logic (same as before)
                 raw_en_name = clean_en_name
                 if len(raw_en_name) > 50 or re.search(r'[\u4e00-\u9fff]', raw_en_name):
                    continue
                 canonical_name = raw_en_name[0].upper() + raw_en_name[1:]

            current_drug = canonical_name
            
            drugs[current_drug] = {
                "category": current_category,
                "points": []
            }
            continue
            


    return drugs

def main():
    all_drugs = {}
    
    # Load data.json for name mapping
    with open('src/data.json', 'r', encoding='utf-8') as f:
        data_json = json.load(f)
    
    # helper maps
    cn_map = {d['cn']: d['en'] for d in data_json if 'cn' in d and 'en' in d}
    en_map = {d['en'].lower(): d['en'] for d in data_json if 'en' in d}

    # List files numeric sort
    files = [f for f in os.listdir(PPT_CONTENT_DIR) if f.endswith('.md')]
    # simple sort by number
    files.sort(key=lambda x: int(x.split('.')[0]))

    for filename in files:
        filepath = os.path.join(PPT_CONTENT_DIR, filename)
        print(f"Processing {filename}...")
        parsed = parse_markdown_file(filepath, cn_map, en_map)
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
