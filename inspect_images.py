import sys
sys.path.append('.')
from backend.services.scraper import BRANDS_CATEGORIES, get_product_image

print("Checking product image assignments:")
all_images = {}
duplicates = {}

for category, brands in BRANDS_CATEGORIES.items():
    print(f"\n--- Category: {category} ---")
    for brand, models in brands.items():
        for model in models:
            full_name = f"{brand} {model}"
            img = get_product_image(full_name, category)
            print(f"{full_name}: {img}")
            if img in all_images:
                all_images[img].append(full_name)
            else:
                all_images[img] = [full_name]

print("\n--- Duplicated Images ---")
for img, products in all_images.items():
    if len(products) > 1:
        print(f"\nImage: {img}")
        print(f"Used by: {', '.join(products)}")
