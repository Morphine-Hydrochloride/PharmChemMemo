import json
import os

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'src', 'data.json')
IMAGES_DIR = os.path.join(BASE_DIR, 'public', 'assets', 'images')

def check_images():
    if not os.path.exists(DATA_PATH):
        print(f"Error: data.json not found at {DATA_PATH}")
        return

    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading data.json: {e}")
        return

    missing_images = []
    total_images = 0

    print(f"Checking images for {len(data)} items...")

    for item in data:
        image_path = item.get('image')
        if not image_path:
            continue
        
        total_images += 1
        
        # Determine local file path
        # image_path in json is typically "/assets/images/Filename.svg"
        if image_path.startswith('/assets/images/'):
            filename = image_path.replace('/assets/images/', '')
            local_path = os.path.join(IMAGES_DIR, filename)
            
            if not os.path.exists(local_path):
                missing_images.append({
                    'cn': item.get('cn', 'Unknown'),
                    'en': item.get('en', 'Unknown'),
                    'path': image_path,
                    'full_path': local_path
                })
        else:
             print(f"Warning: Unusual image path format for {item.get('en')}: {image_path}")

    print("-" * 30)
    print(f"Total checked: {total_images}")
    print(f"Missing images: {len(missing_images)}")
    print("-" * 30)

    if missing_images:
        print("\nMissing Files Details:")
        for missing in missing_images:
            print(f"- [{missing['cn']} / {missing['en']}] Path: {missing['path']}")
    else:
        print("All image files exist.")

if __name__ == "__main__":
    check_images()
