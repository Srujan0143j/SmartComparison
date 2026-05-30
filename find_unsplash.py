import os
import re

pattern = re.compile(r'https://images\.unsplash\.com/photo-[a-zA-Z0-9\-]+')
urls = set()

for r, d, files in os.walk('.'):
    # Skip virtual environments or cache folders if any
    if 'node_modules' in r or '__pycache__' in r or '.git' in r:
        continue
    for f in files:
        if f.endswith(('.py', '.js', '.html', '.css')):
            path = os.path.join(r, f)
            try:
                content = open(path, 'r', encoding='utf-8').read()
                found = pattern.findall(content)
                for url in found:
                    urls.add(url)
            except Exception as e:
                pass

print(f"Found {len(urls)} unique Unsplash URLs in workspace:")
for u in sorted(urls):
    print(u)
