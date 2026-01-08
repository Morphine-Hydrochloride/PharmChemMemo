import json

def main():
    try:
        data = json.load(open('src/data.json', encoding='utf-8'))
        peth = [d for d in data if 'Pethidine' in d['en']][0]
        s = peth['smiles']
        print(f"SMILES: {s}")
        print(f"Has COC(=O): {'COC(=O)' in s}")
        print(f"Has CCOC(=O): {'CCOC(=O)' in s}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
