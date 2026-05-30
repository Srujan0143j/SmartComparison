import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

categories = {
    "TV": "unsplash smart tv television",
    "Smartwatch": "unsplash smartwatch fitness-band",
    "Monitor": "unsplash computer monitor display screen",
    "Console": "unsplash gaming console playstation xbox",
    "Speaker": "unsplash bluetooth speaker sound",
    "Appliance": "unsplash refrigerator washing-machine microwave",
    "Laptop": "unsplash laptop notebook macbook"
}

photo_pattern = re.compile(r'unsplash\.com/photos/([a-zA-Z0-9\-_]+)')
cdn_pattern = re.compile(r'images\.unsplash\.com/(photo-[a-zA-Z0-9\-_]+)')

collected = {}

for cat, query in categories.items():
    print(f"Searching Yahoo for {cat} images...")
    encoded_query = urllib.parse.quote(query)
    url = f"https://search.yahoo.com/search?p={encoded_query}"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            pids = photo_pattern.findall(html)
            cdns = cdn_pattern.findall(html)
            
            pids = list(set(pids))
            cdns = list(set(cdns))
            
            print(f"  Found {len(pids)} photo IDs, {len(cdns)} CDN IDs for {cat}.")
            
            if cat not in collected:
                collected[cat] = []
            collected[cat].extend(pids)
            collected[cat].extend(cdns)
            
    except Exception as e:
        print(f"  Error: {e}")

print("Done! Collected IDs:")
for c, ids in collected.items():
    print(f"{c}: {list(set(ids))[:10]}")
