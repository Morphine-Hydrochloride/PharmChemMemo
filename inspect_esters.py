import json

def main():
    try:
        data = json.load(open('src/data.json', encoding='utf-8'))
        targets = ['Pethidine hydrochloride', 'Loratadine', 'Enalapril maleate', 'Clofibrate', 'Oseltamivir phosphate']
        
        found = [d for d in data if any(t == d.get('en','') for t in targets)]
        
        for d in found:
            print(f"{d['en']}: {d['smiles']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
