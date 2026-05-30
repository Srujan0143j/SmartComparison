import urllib.request
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/vnd.github.v3+json'
}

queries = [
    'https://api.github.com/search/code?q=images.unsplash.com+laptop+in:file+extension:json',
    'https://api.github.com/search/code?q=images.unsplash.com+monitor+in:file+extension:json',
    'https://api.github.com/search/code?q=images.unsplash.com+watch+in:file+extension:json',
    'https://api.github.com/search/code?q=images.unsplash.com+camera+in:file+extension:json',
    'https://api.github.com/search/code?q=images.unsplash.com+television+in:file+extension:json',
    'https://api.github.com/search/code?q=images.unsplash.com+speaker+in:file+extension:json',
    'https://api.github.com/search/code?q=images.unsplash.com+appliance+in:file+extension:json'
]

unsplash_pattern = re.compile(r'https://images\.unsplash\.com/photo-[a-zA-Z0-9\-]+')

collected = {}

for url in queries:
    category = url.split("+")[1]
    print(f"Searching GitHub for {category}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            items = res.get("items", [])
            print(f"  Found {len(items)} files.")
            for item in items[:3]:  # inspect first 3 files
                raw_url = item.get("html_url", "").replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                print(f"    Reading {raw_url}...")
                try:
                    raw_req = urllib.request.Request(raw_url, headers=headers)
                    with urllib.request.urlopen(raw_req) as raw_resp:
                        content = raw_resp.read().decode('utf-8', errors='ignore')
                        found = unsplash_pattern.findall(content)
                        if found:
                            if category not in collected:
                                collected[category] = []
                            collected[category].extend(found)
                            print(f"      Found {len(found)} Unsplash URLs.")
                except Exception as e:
                    print(f"      Error reading raw file: {e}")
    except Exception as e:
        print(f"  Error searching GitHub: {e}")

with open("github_images.json", "w") as f:
    json.dump(collected, f, indent=4)
print("Done!")
