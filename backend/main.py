from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from backend.database import get_db
from backend.services.scraper import seed_database
from backend.services.ml_engine import ml_engine
from bson import ObjectId

app = FastAPI(
    title="SmartCompare API",
    description="ML & MongoDB based Product Comparison and Analysis Platform",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to serialize MongoDB docs
def serialize_doc(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

@app.on_event("startup")
def startup_event():
    # Only seed database automatically if it is currently empty
    try:
        db = get_db()
        from pymongo.database import Database
        # Check if we are using mock database or real db
        if isinstance(db, Database):
            count = db["products"].count_documents({})
        else:
            # Fallback for mock db
            count = len(db["products"].data)
            
        if count == 0:
            print("Database is empty. Seeding simulated comparison data...")
            seed_database()
        else:
            print(f"Database already contains {count} products. Skipping startup auto-seed.")
    except Exception as e:
        print(f"Error checking/seeding database during startup: {e}")

@app.get("/")
def home():
    return {
        "message": "Welcome to SmartCompare API!",
        "status": "online",
        "endpoints": {
            "categories": "/api/categories",
            "search": "/api/search",
            "compare_stores": "/api/compare/stores?name=Product+Name",
            "compare_models": "/api/compare/models?names=Model1,Model2",
            "seed": "/api/seed (POST)"
        }
    }

@app.post("/api/seed")
def seed_db():
    try:
        db = get_db()
        # Drop collections to fresh seed
        db["products"].delete_many({})
        seed_database()
        return {"status": "success", "message": "Database re-seeded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
def get_categories():
    db = get_db()
    try:
        categories = db["products"].distinct("category")
        return {"categories": categories}
    except Exception as e:
        # If DB error, return static fallback categories
        return {"categories": ["Smartphones", "Laptops", "Headphones", "TVs", "Cameras"]}

def get_specific_search_query(name: str, category: str, specs: dict) -> str:
    import re
    query_parts = [name]
    
    def clean_spec(val):
        if not val:
            return ""
        val = str(val).strip()
        val = re.sub(r'(\d+)\s+(GB|TB)', r'\1\2', val)
        return val

    if category in ["Smartphones", "Laptops"]:
        ram = clean_spec(specs.get("RAM", ""))
        storage = clean_spec(specs.get("Storage", ""))
        if ram:
            query_parts.append(ram)
        if storage:
            query_parts.append(storage)
            
    elif category == "Monitors":
        size = clean_spec(specs.get("Screen Size", ""))
        if size:
            query_parts.append(size)
            
    elif category == "Gaming Consoles":
        storage = clean_spec(specs.get("Storage", ""))
        if storage:
            query_parts.append(storage)
            
    return " ".join(query_parts)

def match_product_name(query_name: str, title: str) -> bool:
    import re
    # Normalize "+" to "plus" for both to handle things like "S26+" vs "S26 Plus"
    q_name = query_name.lower().replace("+", "plus")
    t_name = title.lower().replace("+", "plus")
    
    q_words = q_name.split()
    # Check that all query words are present
    # For digit words, enforce stand-alone matching to prevent e.g. "12" matching inside "512"
    for w in q_words:
        if w.isdigit():
            pattern = r'(?<!\d)' + re.escape(w) + r'(?!\d)'
            if not re.search(pattern, t_name):
                return False
        else:
            if w not in t_name:
                return False
        
    modifiers = ["pro", "max", "plus", "ultra", "lite", "slim", "digital", "fe", "fold", "flip", "active", "classic", "neo", "oled", "qled", "mini"]
    for mod in modifiers:
        pattern = r'\b' + re.escape(mod) + r'\b'
        if re.search(pattern, t_name):
            if not re.search(pattern, q_name):
                return False
                
    for word in q_words:
        if word.isdigit():
            digit_pattern = r'\b(' + word + r'[a-zA-Z]+)\b'
            match = re.search(digit_pattern, t_name)
            if match:
                combined_word = match.group(1)
                if combined_word not in q_name:
                    return False
                    
    # Filter out accessories unless query explicitly asks for them
    accessory_keywords = ["case", "cover", "glass", "protector", "guard", "adapter", "charger", "cable", "film", "shield", "skin", "pouch", "strap", "band", "hood", "tripod", "bag", "mount", "stand"]
    for acc in accessory_keywords:
        pattern = r'\b' + re.escape(acc) + r'\b'
        if re.search(pattern, t_name):
            if not re.search(pattern, q_name):
                return False
                
    return True

def validate_scraped_product(title_or_alt: str, product_name: str, specs: dict, category: str) -> bool:
    import re
    if not title_or_alt:
        return False
        
    # 1. Match product name
    if not match_product_name(product_name, title_or_alt):
        return False
        
    t_lower = title_or_alt.lower()
    
    # 2. Check RAM if present in specs
    if category in ["Smartphones", "Laptops"] and "RAM" in specs:
        ram_val = str(specs["RAM"]).lower().replace(" ", "") # e.g. "16gb"
        ram_num = re.sub(r'[^\d]', '', ram_val)
        
        # Find all RAM-like numbers in the title (numbers <= 64 followed by gb/ram)
        # e.g., "16gb", "16 gb", "16 gb ram"
        ram_matches = re.findall(r'(\d+)\s*(?:gb|ram)\b', t_lower)
        ram_numbers = [m for m in ram_matches if int(m) <= 64]
        
        if ram_numbers:
            # If RAM is mentioned in the title, it must match our RAM
            if ram_num not in ram_numbers:
                return False
                
    # 3. Check Storage if present in specs
    if category in ["Smartphones", "Laptops", "Gaming Consoles"] and "Storage" in specs:
        storage_val = str(specs["Storage"]).lower().replace(" ", "")
        for suffix in ["ssd", "hdd", "emmc"]:
            storage_val = storage_val.replace(suffix, "")
            
        # Find all storage-like values in the title
        storage_matches = []
        gb_matches = re.findall(r'(\d+)\s*gb\b', t_lower)
        for m in gb_matches:
            val = int(m)
            if val >= 128:
                storage_matches.append(str(val) + "gb")
                
        tb_matches = re.findall(r'(\d+)\s*tb\b', t_lower)
        for m in tb_matches:
            val = int(m)
            storage_matches.append(str(val) + "tb")
            if val == 1:
                storage_matches.extend(["1000gb", "1024gb"])
            elif val == 2:
                storage_matches.extend(["2000gb", "2048gb"])
                
        if storage_matches:
            # Our target variants
            target_variants = [storage_val]
            if storage_val == "1tb":
                target_variants.extend(["1000gb", "1024gb"])
            elif storage_val in ["1000gb", "1024gb"]:
                target_variants.append("1tb")
                
            if not any(var in storage_matches for var in target_variants):
                return False
                
    # 4. Check Screen Size for Monitors
    if category == "Monitors" and "Screen Size" in specs:
        screen_size = str(specs["Screen Size"]).lower().replace(" ", "").replace("-", "")
        size_num = re.sub(r'[^\d]', '', screen_size)
        if size_num:
            title_clean = title_or_alt.lower().replace(" ", "").replace("-", "")
            if size_num not in title_clean:
                return False
                
    return True

def update_single_product_live(name: str, category: str, specs: dict, listings: list):
    import datetime
    from bson import ObjectId
    
    now = datetime.datetime.utcnow()
    specific_search_query = get_specific_search_query(name, category, specs)
    
    # Scrape Flipkart and Amazon live concurrently
    import concurrent.futures
    amazon_res = None
    flipkart_res = None
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_amazon = executor.submit(scrape_amazon_live, name, specs, category)
        future_flipkart = executor.submit(scrape_flipkart_live, name, specs, category)
        
        try:
            amazon_res = future_amazon.result(timeout=3.5)
        except Exception as e:
            print(f"Amazon live scrape failed for '{name}': {e}")
        try:
            flipkart_res = future_flipkart.result(timeout=3.5)
        except Exception as e:
            print(f"Flipkart live scrape failed for '{name}': {e}")
            
    amazon_price = amazon_res["price"] if amazon_res else None
    amazon_url = amazon_res["url"] if amazon_res else None
    
    flipkart_price = flipkart_res["price"] if flipkart_res else None
    flipkart_url = flipkart_res["url"] if flipkart_res else None
    
    ref_price = None
    if amazon_price:
        ref_price = amazon_price
    elif flipkart_price:
        ref_price = flipkart_price
        
    # Update prices and URLs in memory and save to MongoDB
    from backend.services.scraper import generate_store_url
    db = get_db()
    
    for l in listings:
        source = l["source"]
        l["last_updated"] = now.isoformat()
        
        if source == "Amazon":
            if amazon_url:
                l["url"] = amazon_url
            elif not l.get("url") or "google.com/search" in l.get("url"):
                l["url"] = generate_store_url(source, specific_search_query, category)
            if amazon_price:
                l["price"] = float(amazon_price)
                
        elif source == "Flipkart":
            if flipkart_url:
                l["url"] = flipkart_url
            elif not l.get("url") or "google.com/search" in l.get("url"):
                l["url"] = generate_store_url(source, specific_search_query, category)
            if flipkart_price:
                l["price"] = float(flipkart_price)
                
        else:
            # For projected stores (Croma, Reliance, Vijay Sales): they use Google site-search redirect
            l["url"] = generate_store_url(source, specific_search_query, category)
            if ref_price:
                if source == "Croma":
                    l["price"] = float(round(ref_price * 1.01, -2))
                elif source == "Reliance Digital":
                    l["price"] = float(round(ref_price * 1.005, -2))
                elif source == "Vijay Sales":
                    l["price"] = float(round(ref_price * 0.995, -2))
                    
        # Save to database
        try:
            products_col = db["products"]
            if hasattr(products_col, "update_one"):
                doc_id = l["_id"]
                if isinstance(doc_id, str) and ObjectId.is_valid(doc_id):
                    match_id = ObjectId(doc_id)
                else:
                    match_id = doc_id
                products_col.update_one(
                    {"_id": match_id},
                    {"$set": {
                        "price": l["price"],
                        "url": l["url"],
                        "last_updated": l["last_updated"]
                    }}
                )
        except Exception as e:
            print(f"Database update error for '{name}': {e}")

def update_prices_for_results(results: list):
    # Group results by product name so we can update them per product
    unique_products = {}
    for r in results:
        name = r["name"]
        if name not in unique_products:
            unique_products[name] = {
                "category": r["category"],
                "specifications": r.get("specifications", {}),
                "listings": []
            }
        unique_products[name]["listings"].append(r)
        
    # Check and update each product
    import datetime
    now = datetime.datetime.utcnow()
    
    # Limit synchronous updates to 3 unique products to avoid Vercel timeouts
    updated_count = 0
    
    for name, info in unique_products.items():
        listings = info["listings"]
        needs_update = False
        
        for l in listings:
            last_upd = l.get("last_updated")
            if not last_upd:
                needs_update = True
                break
            
            if isinstance(last_upd, str):
                try:
                    dt = datetime.datetime.fromisoformat(last_upd)
                except:
                    dt = datetime.datetime.min
            else:
                dt = last_upd
                
            if (now - dt).total_seconds() > 600: # 10 minutes
                needs_update = True
                break
                
        if needs_update:
            if updated_count < 3:
                try:
                    update_single_product_live(name, info["category"], info["specifications"], listings)
                    updated_count += 1
                except Exception as e:
                    print(f"Failed to update '{name}' live: {e}")
            else:
                print(f"Update skipped for '{name}' to preserve response latency.")

@app.get("/api/search")
def search_products(
    q: Optional[str] = Query(None, description="Search term for product name, brand or category"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    db = get_db()
    query = {}
    
    if category:
        query["category"] = category
        
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"brand": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}}
        ]
        
    try:
        cursor = db["products"].find(query)
        results = [serialize_doc(doc) for doc in cursor]
        
        # Apply 10-minute caching checks and fetch live updates if needed
        update_prices_for_results(results)
        
        # Run ML engine on results to score them
        scored_results = ml_engine.score_and_recommend(results)
        
        # Return unique grouped products (just list the models, showing their average rating & price range)
        # to prevent listing "OnePlus 12" 3 times in the general search results.
        grouped_models = {}
        for p in scored_results:
            name = p["name"]
            p_category = p["category"]
            p_specs = p.get("specifications", {})
            spec_query = get_specific_search_query(name, p_category, p_specs)
            
            if p["source"] in ["Amazon", "Flipkart"] and p.get("url") and "google.com/search" not in p["url"]:
                url_to_use = p["url"]
            else:
                from backend.services.scraper import generate_store_url
                url_to_use = generate_store_url(p["source"], spec_query, p_category)
            
            listing_info = {
                "source": p["source"],
                "price": p["price"],
                "url": url_to_use,
                "rating": p["rating"],
                "ml_score": p["ml_score"] or 80.0,
                "ml_label": p["ml_label"] or "Recommended"
            }
            
            if name not in grouped_models:
                grouped_models[name] = {
                    "name": name,
                    "brand": p["brand"],
                    "category": p["category"],
                    "image_url": p["image_url"],
                    "min_price": p["price"],
                    "max_price": p["price"],
                    "avg_rating": p["rating"],
                    "total_reviews": p["review_count"],
                    "stores": [p["source"]],
                    "ml_score": p["ml_score"] or 80.0,
                    "ml_label": p["ml_label"] or "Recommended",
                    "specifications": p["specifications"],
                    
                    # Track best deal (highest ML score)
                    "best_deal_store": p["source"],
                    "best_deal_price": p["price"],
                    "best_deal_url": url_to_use,
                    "best_deal_score": p["ml_score"] or 80.0,
                    "listings": [listing_info]
                }
            else:
                gm = grouped_models[name]
                gm["min_price"] = min(gm["min_price"], p["price"])
                gm["max_price"] = max(gm["max_price"], p["price"])
                gm["avg_rating"] = round((gm["avg_rating"] + p["rating"]) / 2.0, 1)
                gm["total_reviews"] += p["review_count"]
                if p["source"] not in gm["stores"]:
                    gm["stores"].append(p["source"])
                gm["listings"].append(listing_info)
                
                # Update best deal if this listing has a higher ML score
                curr_ml = p["ml_score"] or 80.0
                if curr_ml > gm["best_deal_score"]:
                    gm["best_deal_store"] = p["source"]
                    gm["best_deal_price"] = p["price"]
                    gm["best_deal_url"] = url_to_use
                    gm["best_deal_score"] = curr_ml
                    
        return {"results": list(grouped_models.values()), "raw_count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def scrape_flipkart_live(product_name: str, specs: dict, category: str = ""):
    import requests
    import re
    
    specific_search_query = get_specific_search_query(product_name, category, specs)
    url = f"https://www.flipkart.com/search?q={specific_search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code != 200:
            return None
            
        chunks = r.text.split('<a ')
        for chunk in chunks:
            href_match = re.search(r'^[^>]*href="([^"]+)"', chunk)
            alt_match = re.search(r'alt="([^"]+)"', chunk)
            
            if href_match and alt_match:
                href = href_match.group(1)
                alt = alt_match.group(1).strip()
                
                # Check match using validate_scraped_product
                if validate_scraped_product(alt, product_name, specs, category):
                    price_match = re.search(r'₹([0-9,]+)', chunk)
                    if price_match:
                        price_val = float(re.sub(r'[^\d]', '', price_match.group(1)))
                        cleaned_href = href.replace("&amp;", "&")
                        product_url = "https://www.flipkart.com" + cleaned_href
                        print(f"Flipkart Live Scraper Match: '{alt}' -> Price: {price_val}")
                        return {"price": price_val, "url": product_url}
                        
    except Exception as e:
        print(f"Error scraping Flipkart live: {e}")
    return None

def scrape_amazon_live(product_name: str, specs: dict, category: str = ""):
    import requests
    import re
    
    specific_search_query = get_specific_search_query(product_name, category, specs)
    url = f"https://www.amazon.in/s?k={specific_search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code != 200 or "api-services-support@amazon.com" in r.text:
            return None
            
        chunks = r.text.split('data-component-type="s-search-result"')
        for chunk in chunks[1:]:
            title_match = re.search(r'aria-label="([^"]+)"', chunk)
            if not title_match:
                title_match = re.search(r'class="[^"]*a-text-normal"[^>]*>(?:<span[^>]*>)?([^<]+)', chunk)
                
            price_match = re.search(r'class="a-price-whole">([0-9,]+)', chunk)
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', chunk)
            if not asin_match:
                asin_match = re.search(r'/gp/product/([A-Z0-9]{10})', chunk)
                
            if title_match and price_match and asin_match:
                title = title_match.group(1).strip()
                price_val = float(re.sub(r'[^\d]', '', price_match.group(1)))
                asin = asin_match.group(1)
                product_url = f"https://www.amazon.in/dp/{asin}"
                
                # Check match using validate_scraped_product
                if validate_scraped_product(title, product_name, specs, category):
                    print(f"Amazon Live Scraper Match: '{title}' -> Price: {price_val}")
                    return {"price": price_val, "url": product_url}
                    
    except Exception as e:
        print(f"Error scraping Amazon live: {e}")
    return None

def filter_realistic_price(prices, base_db_price):
    if not prices:
        return None
    # Try to find a price within 30% of base price
    for p in prices:
        if base_db_price * 0.70 <= p <= base_db_price * 1.30:
            return float(p)
    # Try to find a price within 40% of base price
    for p in prices:
        if base_db_price * 0.60 <= p <= base_db_price * 1.40:
            return float(p)
    return float(prices[0]) if prices else None

@app.get("/api/compare/stores")
def compare_stores(name: str = Query(..., description="Exact name of the product model to compare across stores")):
    db = get_db()
    try:
        # Find all listings of this exact product model across stores using a regex-resilient lookup
        import re
        escaped_name = re.escape(name).replace(r"\ ", ".*")
        cursor = db["products"].find({"name": {"$regex": f"^{escaped_name}$", "$options": "i"}})
        listings = [serialize_doc(doc) for doc in cursor]
        
        if not listings:
            raise HTTPException(status_code=404, detail=f"Product model '{name}' not found.")
            
        # Apply 10-minute caching checks and fetch live updates if needed
        update_prices_for_results(listings)

        # Analyze using ML engine with the updated real-time prices
        compared_listings = ml_engine.score_and_recommend(listings)
        
        # Sort by ML score (descending)
        compared_listings.sort(key=lambda x: x["ml_score"], reverse=True)
        
        return {
            "product_name": name,
            "category": listings[0]["category"],
            "brand": listings[0]["brand"],
            "specifications": listings[0]["specifications"],
            "listings": compared_listings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compare/models")
def compare_models(names: str = Query(..., description="Comma separated list of product names to compare side by side")):
    db = get_db()
    product_names = [n.strip() for n in names.split(",") if n.strip()]
    if not product_names:
        raise HTTPException(status_code=400, detail="Please provide at least one product name to compare.")
        
    try:
        comparison_results = []
        for name in product_names:
            # For each product model, get the best store listing (highest ML scored listing)
            cursor = db["products"].find({"name": name})
            listings = [serialize_doc(doc) for doc in cursor]
            
            if listings:
                scored = ml_engine.score_and_recommend(listings)
                scored.sort(key=lambda x: x["ml_score"], reverse=True)
                comparison_results.append(scored[0]) # Get top store listing for that model
                
        # Re-run ML engine on the cross-model choices to compare them together!
        final_comparison = ml_engine.score_and_recommend(comparison_results)
        
        return {
            "comparison": final_comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
