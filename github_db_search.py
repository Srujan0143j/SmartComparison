import urllib.request
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0'
}

# 1. Search for repositories related to "react shopping cart" or "react ecommerce"
search_url = "https://api.github.com/search/repositories?q=react+shopping-cart+stars:>5"
print("Searching repositories...")

pattern = re.compile(r'https://images\.unsplash\.com/photo-[a-zA-Z0-9\-?&=%_.]+')
collected = set()

try:
    req = urllib.request.Request(search_url, headers=headers)
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        repos = res.get("items", [])
        print(f"Found {len(repos)} repositories.")
        
        for repo in repos[:15]:
            full_name = repo.get("full_name")
            default_branch = repo.get("default_branch", "master")
            print(f"Checking {full_name}...")
            
            # Common paths for db.json or products.json
            paths = [
                "db.json",
                "products.json",
                "src/data.js",
                "src/products.json",
                "src/data/products.json",
                "src/data/db.json"
            ]
            
            for path in paths:
                raw_url = f"https://raw.githubusercontent.com/{full_name}/{default_branch}/{path}"
                try:
                    raw_req = urllib.request.Request(raw_url, headers=headers)
                    with urllib.request.urlopen(raw_req) as raw_resp:
                        if raw_resp.status == 200:
                            content = raw_resp.read().decode('utf-8', errors='ignore')
                            found = pattern.findall(content)
                            if found:
                                print(f"  Found {len(found)} Unsplash links in {path}!")
                                for link in found:
                                    # Clean link to get base photo URL
                                    base_link = link.split("?")[0]
                                    collected.add(base_link)
                                break  # found a valid data file, skip other paths for this repo
                except Exception as e:
                    pass
except Exception as e:
    print(f"Error searching repos: {e}")

print(f"Total unique Unsplash base URLs collected: {len(collected)}")
for l in sorted(collected):
    print(l)

with open("collected_unsplash.json", "w") as f:
    json.dump(list(collected), f, indent=4)
