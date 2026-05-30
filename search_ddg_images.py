import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

categories = {
    "Laptops": "images.unsplash.com/photo- laptop notebook",
    "TVs": "images.unsplash.com/photo- television smart-tv",
    "Smartwatches": "images.unsplash.com/photo- smartwatch apple-watch",
    "Speakers": "images.unsplash.com/photo- bluetooth-speaker sound-speaker",
    "Consoles": "images.unsplash.com/photo- playstation-5 xbox nintendo-switch",
    "Appliances": "images.unsplash.com/photo- washing-machine microwave refrigerator",
    "Monitors": "images.unsplash.com/photo- computer-monitor displays-screen"
}

photo_pattern = re.compile(r'images\.unsplash\.com/(photo-[a-zA-Z0-9\-]+)')

for cat, query in categories.items():
    print(f"Searching DuckDuckGo for {cat} images...")
    encoded_query = urllib.parse.quote(query)
    # Using Lite DDG search which is cleaner and less likely to block
    url = f"https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
            found = photo_pattern.findall(html)
            unique_found = list(set(found))
            print(f"  Found {len(unique_found)} photo IDs for {cat}:")
            for pid in unique_found[:10]:
                print(f"    - {pid}")
    except Exception as e:
        print(f"  Error: {e}")
