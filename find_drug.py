import json

try:
    with open(r'c:\Users\24550\Downloads\不背药化V2.1\不背药化\local_project\src\data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    found = False
    for item in data:
        if 'Pentazocine' in item.get('en', '') or '喷他佐辛' in item.get('cn', ''):
            print(json.dumps(item, indent=2, ensure_ascii=False))
            found = True
            
    if not found:
        print("Not found")
except Exception as e:
    print(f"Error: {e}")
