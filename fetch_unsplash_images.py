import urllib.request
import re
import json
import time

CATEGORIES = {
    "Smartphones": "smartphone",
    "Laptops": "laptop",
    "Headphones": "headphones",
    "TVs": "smart-tv",
    "Cameras": "camera",
    "Smartwatches": "smartwatch",
    "Audio Speakers": "bluetooth-speaker",
    "Gaming Consoles": "gaming-console",
    "Appliances": "home-appliances",
    "Monitors": "computer-monitor"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

collected_urls = {}

for cat_name, query in CATEGORIES.items():
    print(f"Fetching images for {cat_name} (query: {query})...")
    url = f"https://unsplash.com/s/photos/{query}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
        
        # Look for images.unsplash.com/photo-... URLs
        # Typically they look like: https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=...
        pattern = r'https://images\.unsplash\.com/photo-[a-zA-Z0-9\-]+'
        urls = re.findall(pattern, html)
        
        # Deduplicate and keep them clean
        unique_urls = list(set(urls))
        # Filter out very short or invalid ones
        unique_urls = [u for u in unique_urls if len(u.split('/')[-1]) > 10]
        
        collected_urls[cat_name] = unique_urls
        print(f"  Found {len(unique_urls)} images.")
        time.sleep(1) # Be polite
    except Exception as e:
        print(f"  Error fetching {cat_name}: {e}")

# Save to json file
with open('unsplash_pools.json', 'w') as f:
    json.dump(collected_urls, f, indent=4)
print("Done! Saved to unsplash_pools.json")
