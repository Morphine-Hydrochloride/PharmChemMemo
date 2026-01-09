
import json
import time

def add_cache_busting():
    timestamp = int(time.time())
    print(f"Applying timestamp: {timestamp}")
    
    try:
        with open('src/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        count = 0
        for d in data:
            if 'image' in d:
                # Remove old query params if any
                base_url = d['image'].split('?')[0]
                d['image'] = f"{base_url}?v={timestamp}"
                count += 1
                
        with open('src/data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Updated {count} image URLs with cache busting timestamp.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_cache_busting()
