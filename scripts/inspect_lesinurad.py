import json
import os

with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

found = False
for item in data:
    if "Lesinurad" in item.get('en', '') or "雷シ" in item.get('cn', '') or "Lesinurad" in item.get('id', ''):
        print(json.dumps(item, ensure_ascii=False, indent=2))
        found = True

if not found:
    print("Lesinurad not found in data.json")
