import json

def main():
    try:
        data = json.load(open('src/data.json', encoding='utf-8'))
        
        salts = [d for d in data if '.' in d.get('smiles', '')]
        esters = [d for d in data if 'COC(=O)' in d.get('smiles', '')]
        
        with open('structure_report.txt', 'w', encoding='utf-8') as f:
            f.write(f"--- COMPLEX SALTS ({len(salts)}) ---\n")
            for d in salts:
                f.write(f"{d['en']} ({d['cn']}): {d['smiles']}\n")
                
            f.write(f"\n--- METHYL ESTERS ({len(esters)}) ---\n")
            for d in esters:
                f.write(f"{d['en']} ({d['cn']})\n")
        
        print(f"Report generated: structure_report.txt with {len(salts)} salts and {len(esters)} esters.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
