import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

categories = {
    "TV": "smart tv television",
    "Smartwatch": "smartwatch apple watch galaxy watch",
    "Monitor": "computer monitor display screen",
    "Console": "gaming console playstation xbox nintendo switch",
    "Speaker": "bluetooth speaker jbl marshall bose",
    "Appliance": "washing machine microwave refrigerator vacuum",
    "Laptop": "macbook laptop dell hp lenovo"
}

photo_pattern = re.compile(r'unsplash\.com/photos/([a-zA-Z0-9\-_]+)')

for cat, query in categories.items():
    print(f"Searching DuckDuckGo for {cat} images...")
    search_query = f'site:unsplash.com/photos "{query}"'
    encoded_query = urllib.parse.quote(search_query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
            found = photo_pattern.findall(html)
            unique_found = list(set(found))
            print(f"  Found {len(unique_found)} photo IDs for {cat}:")
            for pid in unique_found[:15]:
                print(f"    - {pid}")
    except Exception as e:
        print(f"  Error: {e}")
