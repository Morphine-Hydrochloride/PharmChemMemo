import json
import os

with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    if "红霉素" in item.get('cn', '') or "Erythromycin" in item.get('en', ''):
        print(json.dumps(item, ensure_ascii=False, indent=2))
