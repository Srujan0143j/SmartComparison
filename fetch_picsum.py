import urllib.request
import json
import re

collected_ids = []

for page in range(1, 10):
    url = f"https://picsum.photos/v2/list?page={page}&limit=100"
    print(f"Fetching page {page}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            for item in data:
                download_url = item.get("download_url", "")
                # Format is typically: https://picsum.photos/id/10/2500/1667
                # Or sometimes direct unsplash urls
                # Let's extract the Unsplash ID
                # Picsum ID maps directly to Unsplash ID/photo path in many cases, or we can use the unsplash_url field if available
                unsplash_url = item.get("url", "")
                if "unsplash.com" in unsplash_url:
                    # e.g., https://unsplash.com/photos/yC-Yzbqy7PY
                    photo_id = unsplash_url.split("/")[-1]
                    if photo_id:
                        collected_ids.append({
                            "id": photo_id,
                            "url": f"https://images.unsplash.com/photo-{photo_id}" if not photo_id.startswith("photo-") else f"https://images.unsplash.com/{photo_id}",
                            "author": item.get("author")
                        })
    except Exception as e:
        print(f"Error: {e}")

print(f"Collected {len(collected_ids)} unique image records from Picsum.")
with open("picsum_images.json", "w") as f:
    json.dump(collected_ids, f, indent=4)
