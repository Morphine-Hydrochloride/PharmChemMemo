import json

def main():
    try:
        data = json.load(open('src/data.json', encoding='utf-8'))
        targets = [d for d in data if 'acetate' in d.get('en', '').lower() or '醋酸' in d.get('cn', '')]
        
        with open('acetate_report.txt', 'w', encoding='utf-8') as f:
            f.write(f"--- ACETATE DRUGS ({len(targets)}) ---\n")
            for d in targets:
                f.write(f"{d['en']} ({d['cn']}): {d['smiles']}\n")
        print("Report generated: acetate_report.txt")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
