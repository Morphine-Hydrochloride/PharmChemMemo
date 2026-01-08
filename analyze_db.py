import json

# 读取data.json
with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 按章节整理药物
chapters = {}
for drug in data:
    ch = drug['chapter']
    if ch not in chapters:
        chapters[ch] = {'master': [], 'familiarize': []}
    chapters[ch][drug['type']].append(drug['cn'])

# 输出
for ch in sorted(chapters.keys()):
    print(f'\n=== {ch} ===')
    print(f'掌握: {chapters[ch]["master"]}')
    print(f'熟悉: {chapters[ch]["familiarize"]}')
