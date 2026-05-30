import urllib.request
import re
import json

urls = [
    "https://raw.githubusercontent.com/gip3/react-ecommerce/master/db.json",
    "https://raw.githubusercontent.com/zainkeepscode/react-shopping-cart/master/db.json",
    "https://raw.githubusercontent.com/adrianhajdin/project_nextjs_13_usestate/main/constants/index.ts",
    "https://raw.githubusercontent.com/Arcturus02/ecommerce-website/main/src/data.js",
    "https://raw.githubusercontent.com/jeffrey-lueloff/ecommerce-mock-api/master/db.json"
]

pattern = re.compile(r'https://images\.unsplash\.com/photo-[a-zA-Z0-9\-?&=%_.]+')

collected = set()

for url in urls:
    print(f"Fetching {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8', errors='ignore')
            found = pattern.findall(content)
            print(f"  Found {len(found)} Unsplash links.")
            for link in found:
                collected.add(link)
    except Exception as e:
        print(f"  Error: {e}")

print(f"Total unique Unsplash links collected: {len(collected)}")
for l in sorted(collected)[:50]:
    print(l)
