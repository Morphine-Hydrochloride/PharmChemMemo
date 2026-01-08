import json

with open('src/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

missing_smiles = []
using_png = []

for item in data:
    name = item.get('cn', 'Unknown')
    en_name = item.get('en', 'Unknown')
    smiles = item.get('smiles', '')
    image = item.get('image', '')
    
    if not smiles:
        missing_smiles.append(f"{name} ({en_name})")
    
    if image.endswith('.png') or image.endswith('.jpg') or image.endswith('.jpeg'):
        using_png.append(f"{name} ({en_name}): {image}")

print("=== Missing SMILES ===")
for i in missing_smiles:
    print(i)

print("\n=== Using Raster Image (PNG/JPG) ===")
for i in using_png:
    print(i)
