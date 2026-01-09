import os
import json
import re

def normalize_name(name):
    if not name: return ""
    name = name.lower()
    # List of suffixes to remove
    suffixes = [
        " hydrochloride", " hcl", " sodium", " besylate", " tartrate", 
        " maleate", " phosphate", " acetate", " bromide", " nitrate",
        " salicylate", " citrate", " oxalate", " sulfate", " besilate",
        " 具有.*", " ppt.*", " 盐酸", " 钠", " 琥珀酸", " 枸橼酸", " 顺丁烯二酸", " 磷酸", " 醋酸", " 溴", " 硝酸", " 硫酸", " 草酸", " 苯磺酸", " 重酒石酸"
    ]
    for s in suffixes:
        name = re.sub(s, '', name)
    
    # Remove any extra info in parentheses or after slashes manually (without regex sub for stability)
    if '(' in name:
        name = name.split('(')[0]
    if '（' in name:
        name = name.split('（')[0]
    if '/' in name:
        name = name.split('/')[0]
    if '，' in name:
        name = name.split('，')[0]
    if ',' in name:
        name = name.split(',')[0]
        
    return name.strip()

def extract_ppt_drugs(ppt_dir):
    drugs = []
    pattern = re.compile(r'\*\*([^*]+) \(([^)]+)\)\*\*')
    for filename in os.listdir(ppt_dir):
        if filename.endswith('.md'):
            with open(os.path.join(ppt_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()
                matches = pattern.findall(content)
                for cn, en in matches:
                    cn = cn.strip()
                    en = en.strip()
                    en_parts = re.split(r' / |，|,', en)
                    for part in en_parts:
                        drugs.append({
                            'cn': cn,
                            'en': part.strip(),
                            'file': filename
                        })
    return drugs

def get_db_drugs(data_json_path, keypoints_js_path):
    with open(data_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data_ens = {item['en'].lower(): item for item in data}
        data_cns = {item['cn']: item['en'] for item in data}
        norm_ens = {normalize_name(en): en for en in data_ens.keys()}
        norm_cns = {normalize_name(cn): cn for cn in data_cns.keys()}
    
    with open(keypoints_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
        kp_ens = re.findall(r'"([^"]+)": \[', content)
        kp_ens_lower = {en.lower() for en in kp_ens}
        norm_kp_ens = {normalize_name(en): en for en in kp_ens}
    
    return data_ens, data_cns, kp_ens_lower, norm_ens, norm_cns, norm_kp_ens

def main():
    ppt_dir = 'ppt_content'
    data_json = 'src/data.json'
    keypoints_js = 'src/keyPointsData.js'
    
    ppt_drugs = extract_ppt_drugs(ppt_dir)
    data_ens, data_cns, kp_ens, norm_ens, norm_cns, norm_kp_ens = get_db_drugs(data_json, keypoints_js)
    
    missing_in_data = [] 
    missing_in_kp = []   
    
    unique_kp_missing_keys = set()
    unique_data_missing_keys = set()
    
    for drug in ppt_drugs:
        en = drug['en']
        cn = drug['cn']
        en_lower = en.lower()
        if "slide" in en_lower: continue
        
        norm_en = normalize_name(en)
        norm_cn = normalize_name(cn)
        
        exists_in_data = (
            (en_lower in data_ens) or 
            (cn in data_cns) or 
            (norm_en in norm_ens) or 
            (norm_cn in norm_cns) or
            (norm_en in norm_cns)
        )
        
        if not exists_in_data:
            key = (cn, en)
            if key not in unique_data_missing_keys:
                missing_in_data.append(drug)
                unique_data_missing_keys.add(key)
            
        exists_in_kp = (
            (en_lower in kp_ens) or 
            (norm_en in norm_kp_ens) or
            (cn in norm_kp_ens) or
            (norm_cn in norm_kp_ens)
        )
        
        if not exists_in_kp:
            key = (cn, en)
            if key not in unique_kp_missing_keys:
                missing_in_kp.append({
                    'cn': cn,
                    'en': en,
                    'file': drug['file'],
                    'in_data_json': "Yes" if exists_in_data else "No"
                })
                unique_kp_missing_keys.add(key)
    
    with open('scripts/missing_drugs_report.md', 'w', encoding='utf-8') as f:
        f.write("# Missing Drug Data Report (Refined)\n\n")
        f.write("This report lists drugs identified in the `ppt_content/*.md` files that are missing from the application's databases after careful normalization and synonym checking.\n\n")
        
        f.write("## 1. Drugs Missing from Database entirely (No Card)\n")
        f.write("| Chinese Name | English Name | PPT File | Reason |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for d in missing_in_data:
            f.write(f"| {d['cn']} | {d['en']} | {d['file']} | Not found in `data.json` |\n")
        
        f.write("\n## 2. Drugs Missing Descriptions (Key Points)\n")
        f.write("| Chinese Name | English Name | PPT File | In `data.json`? | Reason |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for d in missing_in_kp:
            f.write(f"| {d['cn']} | {d['en']} | {d['file']} | {d['in_data_json']} | Not found in `keyPointsData.js` |\n")
            
    print("Report generated: scripts/missing_drugs_report.md")

if __name__ == "__main__":
    main()
