import json

def main():
    try:
        data = json.load(open('src/data.json', encoding='utf-8'))
        
        target = [d for d in data if 'Methyldopa' in d['en']][0]
        print(f"Name: {target['en']}")
        print(f"SMILES: {target['smiles']}")
        
        if "COC(=O)" in target['smiles']:
             print("ALERT: Still contains Methyl Ester group!")
        elif "C(O)=O" in target['smiles']:
             print("CONFIRMED: Contains Carboxylic Acid group.")
        else:
             print("STATUS: Unknown structure pattern.")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
