import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote("unsplash refrigerator")
print(f"Fetching {url}...")

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8', errors='ignore')
        
        # Let's find all hrefs in the page
        hrefs = re.findall(r'href="([^"]+)"', html)
        print(f"Found {len(hrefs)} total links.")
        
        unsplash_links = []
        for href in hrefs:
            # DuckDuckGo links are often wrapped, e.g. /l/?kh=-1&uddg=https%3A%2F%2Funsplash.com%2Fphotos%2F...
            if "unsplash.com" in href:
                unsplash_links.append(href)
                print(f"Unsplash Link: {href}")
                
            # If wrapped, decode it
            match = re.search(r'uddg=([^&]+)', href)
            if match:
                decoded = urllib.parse.unquote(match.group(1))
                if "unsplash.com" in decoded:
                    unsplash_links.append(decoded)
                    print(f"Decoded Link: {decoded}")
except Exception as e:
    print(f"Error: {e}")
