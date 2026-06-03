from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import datetime
import asyncio
from backend.database import get_db
from backend.services.scraper import seed_database, generate_store_url
from backend.services.ml_engine import ml_engine
from bson import ObjectId

class AlertSubscription(BaseModel):
    email_or_phone: str
    channel: str
    product_name: str
    target_price: float
    current_price: float

class RecommendationRequest(BaseModel):
    categories: List[str] = []
    recent_searches: List[str] = []

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

def check_and_trigger_alerts(db, product_name: str, new_price: float, old_price: float):
    import datetime
    try:
        # Find active alerts for this product
        alerts = db["alerts"].find({"product_name": product_name})
        for alert in list(alerts):
            target = alert.get("target_price", 0.0)
            if new_price <= target:
                email_or_phone = alert.get("email_or_phone")
                channel = alert.get("channel", "email")
                
                # Simulate dispatch
                print(f"[ALERT TRIGGERED] Sent {channel} to {email_or_phone}: '{product_name}' dropped to \u20b9{new_price} (Target: \u20b9{target})!")
                
                # Create notification
                notification_doc = {
                    "message": f"Price Drop Alert: '{product_name}' has dropped to \u20b9{int(new_price)}! Your target was \u20b9{int(target)}.",
                    "product_name": product_name,
                    "new_price": new_price,
                    "target_price": target,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
                db["notifications"].insert_one(notification_doc)
                
                # Delete the triggered alert so we don't spam
                db["alerts"].delete_many({"_id": alert["_id"]})
    except Exception as e:
        print(f"Error checking alerts: {e}")

def process_price_update(db, prod, new_price: float):
    import datetime
    now = datetime.datetime.utcnow()
    old_price = prod.get("price", new_price)
    
    # 1. Update current price
    prod["price"] = new_price
    prod["last_updated"] = now.isoformat()
    
    # 2. Append to price history
    history = prod.get("price_history", [])
    today_str = datetime.date(2026, 6, 2).strftime("%Y-%m-%d") # align with mock date
    
    # If history is empty, populate it with mock data leading up to today (90 days)
    if not history:
        history = []
        import math
        import random
        for i in range(89, 0, -1):
            day_str = (datetime.date(2026, 6, 2) - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            weekly_cycle = math.sin(i * (2 * math.pi / 7)) * 0.02
            random_noise = random.uniform(-0.015, 0.015)
            mock_price = float(round(old_price * (1 + weekly_cycle + random_noise), -2))
            history.append({"date": day_str, "price": mock_price})
            
    history.append({"date": today_str, "price": new_price})
    
    # Cap history at 90 items
    if len(history) > 90:
        history = history[-90:]
    prod["price_history"] = history
    
    # 3. Recalculate ML scores
    from backend.services.ml_engine import ml_engine
    scored = ml_engine.score_and_recommend([prod])[0]
    
    # 4. Save to database
    from bson import ObjectId
    try:
        doc_id = prod["_id"]
        if isinstance(doc_id, str) and ObjectId.is_valid(doc_id):
            match_id = ObjectId(doc_id)
        else:
            match_id = doc_id
            
        db["products"].update_one(
            {"_id": match_id},
            {"$set": {
                "price": scored["price"],
                "url": prod.get("url"),
                "image_url": prod.get("image_url"),
                "last_updated": scored["last_updated"],
                "price_history": scored["price_history"],
                "ml_score": scored["ml_score"],
                "best_value_score": scored["best_value_score"],
                "ml_sentiment": scored["ml_sentiment"],
                "ml_label": scored["ml_label"],
                "price_prediction": scored["price_prediction"],
                "fake_review_percentage": scored["fake_review_percentage"],
                "reviews": scored["reviews"]
            }}
        )
    except Exception as e:
        print(f"Error saving updated product to DB: {e}")
        
    # 5. Check alerts
    if new_price < old_price:
        check_and_trigger_alerts(db, prod["name"], new_price, old_price)

async def run_periodic_sync():
    print("Background Sync Task: Price synchronization and alerts checking loop started.")
    await asyncio.sleep(10) # Let server start up first
    while True:
        try:
            db = get_db()
            all_prods = db["products"].find({})
            all_prods = list(all_prods)
            if all_prods:
                import random
                # Select up to 6 random products
                batch = random.sample(all_prods, min(len(all_prods), 6))
                print(f"[BACKGROUND SYNC] Running sync check on {len(batch)} products...")
                for prod in batch:
                    current_price = prod.get("price")
                    if current_price:
                        roll = random.random()
                        if roll < 0.4:
                            # Price drops
                            pct = random.uniform(0.015, 0.04)
                            new_price = round(current_price * (1 - pct), -2)
                        elif roll < 0.8:
                            # Price increases
                            pct = random.uniform(0.01, 0.02)
                            new_price = round(current_price * (1 + pct), -2)
                        else:
                            new_price = current_price
                        
                        if new_price != current_price:
                            process_price_update(db, prod, float(new_price))
        except Exception as e:
            print(f"Error in background sync: {e}")
            
        await asyncio.sleep(180) # Sleep for 3 minutes

@app.on_event("startup")
def startup_event():
    # Start background loop
    asyncio.create_task(run_periodic_sync())
    
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
    amazon_img = amazon_res["image_url"] if (amazon_res and "image_url" in amazon_res) else None
    
    flipkart_price = flipkart_res["price"] if flipkart_res else None
    flipkart_url = flipkart_res["url"] if flipkart_res else None
    flipkart_img = flipkart_res["image_url"] if (flipkart_res and "image_url" in flipkart_res) else None
    
    ref_price = None
    if amazon_price:
        ref_price = amazon_price
    elif flipkart_price:
        ref_price = flipkart_price
        
    best_img = amazon_img or flipkart_img
        
    # Update prices and URLs in memory and save to MongoDB
    from backend.services.scraper import generate_store_url
    db = get_db()
    
    for l in listings:
        source = l["source"]
        l["last_updated"] = now.isoformat()
        # Do not use real product images, preserve original mockup images instead
        # if best_img:
        #     l["image_url"] = best_img
        
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
            if "price" in l and l["price"] is not None:
                process_price_update(db, l, float(l["price"]))
        except Exception as e:
            print(f"Database update error for '{name}': {e}")

def run_updates_sync_task(unique_products: dict):
    from backend.database import IS_VERCEL
    if IS_VERCEL:
        print("Running on Vercel. Skipping live scraping.")
        return
        
    import datetime
    now = datetime.datetime.utcnow()
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

def update_prices_for_results(results: list, background_tasks = None):
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
        
    if background_tasks:
        background_tasks.add_task(run_updates_sync_task, unique_products)
    else:
        run_updates_sync_task(unique_products)

@app.get("/api/search")
def search_products(
    background_tasks: BackgroundTasks,
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
        
        # Only run live updates and ML re-scoring for targeted queries to make empty search (homepage load) instant
        if q or category:
            update_prices_for_results(results, background_tasks)
            scored_results = ml_engine.score_and_recommend(results)
        else:
            scored_results = results
        
        # Return unique grouped products (just list the models, showing their average rating & price range)
        # to prevent listing "OnePlus 12" 3 times in the general search results.
        grouped_models = {}
        for p in scored_results:
            name = p["name"]
            p_category = p["category"]
            p_specs = p.get("specifications", {})
            spec_query = get_specific_search_query(name, p_category, p_specs)
            
            # Always generate Google site search URL
            from backend.services.scraper import generate_store_url
            url_to_use = generate_store_url(p["source"], spec_query, p_category)
            
            price_to_use = p["price"]
                
            listing_info = {
                "source": p["source"],
                "price": price_to_use,
                "url": url_to_use,
                "rating": p["rating"],
                "ml_score": p["ml_score"] or 80.0,
                "ml_label": p["ml_label"] or "Recommended"
            }
            
            has_price = price_to_use is not None
            
            if name not in grouped_models:
                grouped_models[name] = {
                    "name": name,
                    "brand": p["brand"],
                    "category": p["category"],
                    "image_url": p["image_url"],
                    "min_price": price_to_use if has_price else None,
                    "max_price": price_to_use if has_price else None,
                    "avg_rating": p["rating"],
                    "total_reviews": p["review_count"],
                    "stores": [p["source"]],
                    "ml_score": p["ml_score"] or 80.0,
                    "ml_label": p["ml_label"] or "Recommended",
                    "specifications": p["specifications"],
                    
                    # Track best deal (highest ML score with price)
                    "best_deal_store": p["source"] if has_price else None,
                    "best_deal_price": price_to_use if has_price else None,
                    "best_deal_url": url_to_use,
                    "best_deal_score": p["ml_score"] if has_price else 0,
                    "listings": [listing_info]
                }
            else:
                gm = grouped_models[name]
                if has_price:
                    if gm["min_price"] is None or gm["min_price"] == 0:
                        gm["min_price"] = price_to_use
                    else:
                        gm["min_price"] = min(gm["min_price"], price_to_use)
                        
                    if gm["max_price"] is None or gm["max_price"] == 0:
                        gm["max_price"] = price_to_use
                    else:
                        gm["max_price"] = max(gm["max_price"], price_to_use)
                        
                gm["avg_rating"] = round((gm["avg_rating"] + p["rating"]) / 2.0, 1)
                gm["total_reviews"] += p["review_count"]
                if p["source"] not in gm["stores"]:
                    gm["stores"].append(p["source"])
                gm["listings"].append(listing_info)
                
                # Update best deal if this listing has a higher ML score and a valid price
                if has_price:
                    curr_ml = p["ml_score"] or 80.0
                    if gm["best_deal_store"] is None or curr_ml > gm["best_deal_score"]:
                        gm["best_deal_store"] = p["source"]
                        gm["best_deal_price"] = price_to_use
                        gm["best_deal_url"] = url_to_use
                        gm["best_deal_score"] = curr_ml
        # Sort grouped models by ML score descending so the best products are recommended first
        results_list = list(grouped_models.values())
        results_list.sort(key=lambda x: x.get("ml_score", 0.0), reverse=True)
        return {"results": results_list, "raw_count": len(results)}
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
                        img_match = re.search(r'<img[^>]*src="([^"]+)"', chunk)
                        img_url = img_match.group(1) if img_match else None
                        print(f"Flipkart Live Scraper Match: '{alt}' -> Price: {price_val}")
                        return {"price": price_val, "url": product_url, "image_url": img_url}
                        
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
                    img_match = re.search(r'class="s-image"[^>]*src="([^"]+)"', chunk)
                    if not img_match:
                        img_match = re.search(r'<img[^>]*src="([^"]+)"', chunk)
                    img_url = img_match.group(1) if img_match else None
                    print(f"Amazon Live Scraper Match: '{title}' -> Price: {price_val}")
                    return {"price": price_val, "url": product_url, "image_url": img_url}
                    
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
def compare_stores(
    background_tasks: BackgroundTasks,
    name: str = Query(..., description="Exact name of the product model to compare across stores")
):
    db = get_db()
    try:
        # Find all listings of this exact product model across stores using a regex-resilient lookup
        import re
        escaped_name = re.escape(name).replace(r"\ ", ".*")
        cursor = db["products"].find({"name": {"$regex": f"^{escaped_name}$", "$options": "i"}})
        listings = [serialize_doc(doc) for doc in cursor]
        
        if not listings:
            raise HTTPException(status_code=404, detail=f"Product model '{name}' not found.")
            
        # Apply 10-minute caching checks and fetch live updates if needed in background
        update_prices_for_results(listings, background_tasks)

        # Clean/generate URLs on the fly for all listings
        from backend.services.scraper import generate_store_url
        for l in listings:
            spec_query = get_specific_search_query(l["name"], l["category"], l.get("specifications", {}))
            l["url"] = generate_store_url(l["source"], spec_query, l["category"])

        # Analyze using ML engine with the updated real-time prices
        compared_listings = ml_engine.score_and_recommend(listings)
        
        # Prices are kept to compare stores accurately
        
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
                # Clean/generate URLs on the fly for all listings
                from backend.services.scraper import generate_store_url
                for l in listings:
                    spec_query = get_specific_search_query(l["name"], l["category"], l.get("specifications", {}))
                    l["url"] = generate_store_url(l["source"], spec_query, l["category"])
                
                prices = [l["price"] for l in listings if "price" in l and l["price"] is not None]
                min_p = min(prices) if prices else 0
                max_p = max(prices) if prices else 0
                
                scored = ml_engine.score_and_recommend(listings)
                
                # Representative store must be Amazon or Flipkart
                real_listings = [l for l in scored if l["source"] in ["Amazon", "Flipkart"]]
                if real_listings:
                    real_listings.sort(key=lambda x: x["ml_score"], reverse=True)
                    best_listing = real_listings[0]
                else:
                    scored.sort(key=lambda x: x["ml_score"], reverse=True)
                    best_listing = scored[0]
                
                # Prices are kept to compare models accurately
                        
                best_listing["min_price"] = min_p
                best_listing["max_price"] = max_p
                comparison_results.append(best_listing) # Get top store listing for that model
                
        # Re-run ML engine on the cross-model choices to compare them together!
        final_comparison = ml_engine.score_and_recommend(comparison_results)
        
        return {
            "comparison": final_comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alerts/subscribe")
def subscribe_alert(sub: AlertSubscription):
    db = get_db()
    try:
        alert_doc = {
            "email_or_phone": sub.email_or_phone,
            "channel": sub.channel,
            "product_name": sub.product_name,
            "target_price": sub.target_price,
            "current_price": sub.current_price,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        db["alerts"].insert_one(alert_doc)
        return {"status": "success", "message": f"Successfully subscribed to alert for {sub.product_name}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notifications")
def get_notifications():
    db = get_db()
    try:
        notifications = db["notifications"].find({})
        notifications = list(notifications)
        # Sort notifications in memory by descending timestamp
        notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"notifications": notifications[:10]}
    except Exception as e:
        return {"notifications": []}

@app.post("/api/recommendations")
def get_recommendations(req: RecommendationRequest):
    db = get_db()
    try:
        categories = [c.strip() for c in req.categories if c.strip()]
        searches = [s.strip().lower() for s in req.recent_searches if s.strip()]
        
        products = []
        if categories:
            # Query top 15 products per category from user history to keep it fast
            for cat in categories[:3]:
                cursor = db["products"].find({"category": cat}).sort([("ml_score", -1)]).limit(15)
                products.extend([serialize_doc(doc) for doc in cursor])
        
        # If no category history or no products match, fetch the top-scoring product from diverse categories
        if not products:
            default_cats = ["Smartphones", "Laptops", "Headphones", "TVs"]
            for cat in default_cats:
                cursor = db["products"].find({"category": cat}).sort([("ml_score", -1)]).limit(1)
                products.extend([serialize_doc(doc) for doc in cursor])
            
        grouped = {}
        for p in products:
            name = p["name"]
            score = p.get("best_value_score") or p.get("ml_score") or 80.0
            
            # Boost if matching recent search terms
            match_score = 0
            if searches:
                for term in searches:
                    if term in name.lower() or term in p.get("brand", "").lower():
                        match_score += 15
            
            p["reco_priority_score"] = score + match_score
            
            if name not in grouped or p["reco_priority_score"] > grouped[name]["reco_priority_score"]:
                grouped[name] = p
                
        recos = list(grouped.values())
        recos.sort(key=lambda x: x.get("reco_priority_score", 0.0), reverse=True)
        
        formatted_recos = []
        for r in recos[:4]:
            price_val = r["price"]
                
            formatted_recos.append({
                "name": r["name"],
                "brand": r["brand"],
                "category": r["category"],
                "image_url": r["image_url"],
                "price": price_val,
                "best_value_score": r.get("best_value_score") or r.get("ml_score") or 80.0,
                "ml_label": r.get("ml_label", "Recommended")
            })
            
        return {"recommendations": formatted_recos}
    except Exception as e:
        return {"recommendations": []}

class AIAssistantRequest(BaseModel):
    query: str

@app.post("/api/ai-assistant")
def ai_assistant(req: AIAssistantRequest):
    import re
    query_lower = req.query.lower()
    
    # 1. Budget extraction
    budget = None
    budget_type = "under"
    if any(w in query_lower for w in ["above", "over", "more than", "greater than", "higher than", "at least", "minimum", "min", "starting from", "starting at", "start from"]):
        budget_type = "above"

    k_match = re.search(r'\b(\d+(?:\.\d+)?)\s*k\b', query_lower)
    if k_match:
        budget = float(k_match.group(1)) * 1000
    else:
        lakh_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:lakh|l)\b', query_lower)
        if lakh_match:
            budget = float(lakh_match.group(1)) * 100000
        else:
            num_match = re.search(r'\b(?:under|below|less than|within|above|over|more than|greater than|at least|min|max|start|starting|at|budget|price|cost|rs\.?|₹)\s*(?:\u20b9|rs\.?)?\s*(\d{4,6})\b', query_lower)
            if num_match:
                budget = float(num_match.group(1))
                
    # 2. Category detection
    category = None
    if any(w in query_lower for w in ["phone", "smartphone", "mobile"]):
        category = "Smartphones"
    elif any(w in query_lower for w in ["laptop", "pc", "macbook", "computer", "notebook"]):
        category = "Laptops"
    elif any(w in query_lower for w in ["headphone", "earphone", "buds", "airpods"]):
        category = "Headphones"
    elif any(w in query_lower for w in ["tv", "television", "smart tv"]):
        category = "TVs"
    elif any(w in query_lower for w in ["camera", "dslr", "lens", "shoot"]):
        category = "Cameras"
    elif any(w in query_lower for w in ["watch", "smartwatch", "band"]):
        category = "Smartwatches"
    elif any(w in query_lower for w in ["speaker", "soundbar", "audio"]):
        category = "Audio Speakers"
    elif any(w in query_lower for w in ["console", "playstation", "ps5", "xbox", "nintendo", "switch"]):
        category = "Gaming Consoles"
    elif any(w in query_lower for w in ["vacuum", "purifier", "dryer", "refrigerator", "fridge", "washer", "washing machine", "microwave", "appliance"]):
        category = "Appliances"
    elif any(w in query_lower for w in ["monitor", "display"]):
        category = "Monitors"
        
    # 1.5 Implicit budgets (if query contains "cheap", "budget", "affordable" but no explicit budget is specified)
    is_cheap_query = any(w in query_lower for w in ["cheap", "affordable", "low cost", "budget", "low price"])
    if not budget and is_cheap_query:
        if category == "Smartphones":
            budget = 20000.0
        elif category == "Laptops":
            budget = 45000.0
        elif category == "Headphones":
            budget = 5000.0
        elif category == "TVs":
            budget = 25000.0
        elif category == "Cameras":
            budget = 50000.0
        elif category == "Smartwatches":
            budget = 5000.0
        elif category == "Audio Speakers":
            budget = 6000.0
        elif category == "Monitors":
            budget = 15000.0
        else:
            budget = 15000.0

    # 3. Use-case detection
    use_cases = []
    if any(w in query_lower for w in ["gaming", "game", "gamer", "gpu", "play"]):
        use_cases.append("gaming")
    if any(w in query_lower for w in ["coding", "programming", "developer", "development", "work", "office", "ram"]):
        use_cases.append("coding")
    if any(w in query_lower for w in ["photo", "photography", "camera", "video", "youtube", "lens"]):
        use_cases.append("photography")
    if any(w in query_lower for w in ["battery", "backup", "long last", "travel", "charge"]):
        use_cases.append("battery")
    if any(w in query_lower for w in ["cheap", "affordable", "value", "best buy"]) or is_cheap_query:
        use_cases.append("value")
        
    # 4. Brand detection
    detected_brand = None
    brands_list = ["apple", "samsung", "oneplus", "google", "sony", "bose", "sennheiser", "jbl", "lg", "xiaomi", "tcl", "hisense", "canon", "nikon", "fujifilm", "panasonic", "garmin", "fitbit", "amazfit", "marshall", "harman kardon", "nintendo", "microsoft", "valve", "asus", "dyson", "philips", "bosch", "hp", "dell", "lenovo", "acer", "nothing", "realme", "motorola", "oppo", "vivo"]
    for b in brands_list:
        if re.search(r'\b' + re.escape(b) + r'\b', query_lower):
            detected_brand = b.capitalize()
            if b == "hp":
                detected_brand = "HP"
            elif b == "lg":
                detected_brand = "LG"
            elif b == "jbl":
                detected_brand = "JBL"
            elif b == "tcl":
                detected_brand = "TCL"
            break

    db = get_db()
    query = {}
    if category:
        query["category"] = category
    if detected_brand:
        query["brand"] = detected_brand
        
    stop_words = {
        "best", "good", "great", "excellent", "under", "below", "less", "than", "within", "budget", 
        "price", "for", "with", "a", "an", "the", "in", "of", "and", "or", "to", "buy", "wait", "want", 
        "need", "find", "show", "me", "rs", "k", "lakh", "device", "devices", "product", "products", 
        "item", "items", "above", "over", "more", "greater", "higher", "at", "least", "minimum", "min",
        "starting", "from", "start", "cheap", "affordable", "low", "cost", "value", "gaming", "game", 
        "gamer", "play", "coding", "programming", "developer", "development", "work", "office", "ram",
        "photo", "photography", "video", "youtube", "battery", "backup", "long", "last", "travel", "charge"
    }
    
    # Exclude all brand names from search keywords
    exclude_words = set(brands_list)
    # Exclude category synonyms
    category_syns = {
        "phone", "smartphone", "mobile", "laptop", "pc", "macbook", "computer", "notebook", 
        "headphone", "earphone", "buds", "airpods", "tv", "television", "smart tv", "camera", 
        "dslr", "lens", "shoot", "watch", "smartwatch", "band", "speaker", "soundbar", "audio", 
        "console", "playstation", "ps5", "xbox", "nintendo", "switch", "vacuum", "purifier", 
        "dryer", "refrigerator", "fridge", "washer", "washing machine", "microwave", "appliance", 
        "monitor", "display", "phones", "smartphones", "mobiles", "laptops", "computers", "notebooks", 
        "headphones", "earphones", "tvs", "televisions", "cameras", "lenses", "watches", "smartwatches", 
        "bands", "speakers", "soundbars", "consoles", "appliances", "monitors", "displays"
    }
    exclude_words.update(category_syns)
    
    # Extract keywords
    words = [w for w in re.findall(r'\b\w+\b', query_lower) if w not in stop_words and w not in exclude_words]
    if words:
        query["$and"] = [{"name": {"$regex": re.escape(w), "$options": "i"}} for w in words]

    try:
        cursor = db["products"].find(query)
        products = [serialize_doc(doc) for doc in cursor]
        
        # Fallback to products matching the category/brand if detected, otherwise all products
        if not products and query:
            fallback_query = {}
            if category:
                fallback_query["category"] = category
            elif detected_brand:
                fallback_query["brand"] = detected_brand
            cursor = db["products"].find(fallback_query)
            products = [serialize_doc(doc) for doc in cursor]
            
        if not products:
            return {"results": []}
            
        # Group products by name
        grouped_models = {}
        for p in products:
            name = p["name"]
            price_val = p["price"]
            has_price = price_val is not None
                
            # Construct listing info for this store listing
            listing_spec_query = get_specific_search_query(name, p["category"], p["specifications"])
            listing_url = generate_store_url(p["source"], listing_spec_query, p["category"])
            listing_price = p["price"]
                
            listing_info = {
                "source": p["source"],
                "price": listing_price,
                "url": listing_url,
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
                    "min_price": price_val if has_price else None,
                    "max_price": price_val if has_price else None,
                    "avg_rating": p["rating"],
                    "total_reviews": p["review_count"],
                    "ml_score": p["ml_score"] or 80.0,
                    "ml_label": p["ml_label"] or "Recommended",
                    "specifications": p["specifications"],
                    "pros": p.get("pros", []),
                    "cons": p.get("cons", []),
                    "review_trust_score": p.get("review_trust_score", 100.0),
                    "price_prediction": p.get("price_prediction", {}),
                    "price_history": p.get("price_history", []),
                    "best_deal_store": p["source"] if has_price else None,
                    "best_deal_price": price_val if has_price else None,
                    "best_deal_url": generate_store_url(p["source"], get_specific_search_query(name, p["category"], p["specifications"]), p["category"]),
                    "best_deal_score": p["ml_score"] if has_price else 0,
                    "listings": [listing_info]
                }
            else:
                gm = grouped_models[name]
                if has_price:
                    if gm["min_price"] is None or gm["min_price"] == 0:
                        gm["min_price"] = price_val
                    else:
                        gm["min_price"] = min(gm["min_price"], price_val)
                        
                    if gm["max_price"] is None or gm["max_price"] == 0:
                        gm["max_price"] = price_val
                    else:
                        gm["max_price"] = max(gm["max_price"], price_val)
                        
                gm["avg_rating"] = round((gm["avg_rating"] + p["rating"]) / 2.0, 1)
                gm["listings"].append(listing_info)
                
                # Check for best deal
                if has_price:
                    curr_ml = p["ml_score"] or 80.0
                    if gm["best_deal_store"] is None or curr_ml > gm["best_deal_score"]:
                        gm["best_deal_store"] = p["source"]
                        gm["best_deal_price"] = price_val
                        gm["best_deal_url"] = generate_store_url(p["source"], get_specific_search_query(name, p["category"], p["specifications"]), p["category"])
                        gm["best_deal_score"] = curr_ml

        # Rank grouped models
        ranked_models = []
        for name, m in grouped_models.items():
            min_p = m["min_price"] or 0
            
            # If we don't have min_p from Amazon/Flipkart, use listing prices
            if min_p == 0:
                all_prices = [p["price"] for p in products if p["name"] == name and p["price"] is not None]
                min_p = min(all_prices) if all_prices else 0
                m["min_price"] = min_p
                m["max_price"] = max(all_prices) if all_prices else 0
                
            # Filter based on budget limit (under/above)
            if budget:
                if budget_type == "under":
                    if min_p == 0 or min_p > budget * 1.1:
                        continue
                elif budget_type == "above":
                    if min_p < budget * 0.9:
                        continue
                
            # Calculate match score starting with ML score
            relevance = m["ml_score"]
            use_case_reasons = []
            spec_highlights = []
            
            # Specs fields parsing
            specs = m["specifications"] or {}
            specs_str = str(specs).lower()
            
            # RAM parsing
            ram_val = specs.get("RAM", specs.get("Memory", ""))
            ram_gb = 0
            if ram_val:
                ram_match = re.search(r'(\d+)\s*gb', str(ram_val).lower())
                if ram_match:
                    ram_gb = int(ram_match.group(1))
                    
            # Megapixels parsing
            cam_val = specs.get("Camera", specs.get("Megapixels", ""))
            cam_mp = 0
            if cam_val:
                cam_match = re.search(r'(\d+)\s*mp', str(cam_val).lower())
                if cam_match:
                    cam_mp = int(cam_match.group(1))
                    
            # Battery parsing
            bat_val = specs.get("Battery", specs.get("Battery Life", ""))
            bat_mah = 0
            if bat_val:
                bat_match = re.search(r'(\d+)\s*mah', str(bat_val).lower())
                if bat_match:
                    bat_mah = int(bat_match.group(1))

            # Graphics card parsing
            gpu_val = specs.get("Graphics", "")
            has_gpu = any(x in str(gpu_val).lower() for x in ["rtx", "gtx", "radeon", "nvidia", "gpu"])
            
            # Processor parsing
            cpu_val = specs.get("Processor", "")
            
            # Refresh rate parsing
            rr_val = specs.get("Refresh Rate", "")
            rr_hz = 0
            if rr_val:
                rr_match = re.search(r'(\d+)\s*hz', str(rr_val).lower())
                if rr_match:
                    rr_hz = int(rr_match.group(1))

            # Budget proximity boost
            if budget:
                if budget_type == "under":
                    if min_p <= budget:
                        relevance += 15
                        if min_p >= budget * 0.7:
                            relevance += 15
                    else:
                        relevance -= 25
                elif budget_type == "above":
                    if min_p >= budget:
                        relevance += 15
                        if min_p <= budget * 1.5:
                            relevance += 15
                    else:
                        relevance -= 25
                    
            # Brand boost
            if detected_brand and m["brand"] == detected_brand:
                relevance += 35
                
            # Category boost
            if category and m["category"] == category:
                relevance += 30
                
            # Use-case matches
            if "gaming" in use_cases:
                if m["category"] == "Laptops":
                    if has_gpu:
                        relevance += 35
                        use_case_reasons.append(f"features a dedicated GPU ({gpu_val}) which is essential for heavy gaming")
                        spec_highlights.append(f"Gaming GPU: {gpu_val}")
                    else:
                        use_case_reasons.append("can run light games, but lacks a high-end dedicated GPU")
                elif m["category"] == "Monitors":
                    if rr_hz >= 120:
                        relevance += 30
                        use_case_reasons.append(f"offers a fast refresh rate of {rr_hz}Hz for smooth visuals")
                        spec_highlights.append(f"Fast {rr_hz}Hz Refresh")
                elif m["category"] == "Smartphones":
                    if ram_gb >= 12:
                        relevance += 25
                        use_case_reasons.append("has massive 12GB+ RAM to prevent gaming lags")
                        spec_highlights.append(f"RAM: {ram_val}")
                elif m["category"] == "Gaming Consoles":
                    relevance += 40
                    use_case_reasons.append("is a specialized system built exclusively for gaming")
                    
            if "coding" in use_cases:
                if m["category"] == "Laptops":
                    if ram_gb >= 16:
                        relevance += 35
                        use_case_reasons.append(f"comes equipped with {ram_gb}GB of RAM which is excellent for running IDEs and virtual machines")
                        spec_highlights.append(f"Multitasking RAM: {ram_val}")
                    else:
                        use_case_reasons.append("is suitable for coding, though a RAM upgrade is recommended for heavy tasks")
                elif m["category"] == "Monitors":
                    use_case_reasons.append("offers crisp resolution and display features to minimize eye fatigue during long coding sessions")
                    
            if "photography" in use_cases:
                if m["category"] == "Cameras":
                    relevance += 40
                    use_case_reasons.append("is a dedicated system featuring advanced lenses for photography")
                elif m["category"] == "Smartphones":
                    if cam_mp >= 48:
                        relevance += 30
                        use_case_reasons.append(f"features an ultra-sharp {cam_val} camera sensor to capture detailed pictures")
                        spec_highlights.append(f"Sharp {cam_val} Camera")
                        
            if "battery" in use_cases:
                if bat_mah >= 5000:
                    relevance += 30
                    use_case_reasons.append(f"carries a massive {bat_mah}mAh battery for multi-day endurance")
                    spec_highlights.append(f"Battery: {bat_val}")
                elif bat_val:
                    relevance += 20
                    use_case_reasons.append(f"offers a long battery life of {bat_val}")
                    spec_highlights.append(f"Endurance: {bat_val}")
                    
            if "value" in use_cases:
                if m["ml_label"] == "Best Value" or m["ml_score"] >= 85:
                    relevance += 25
                    use_case_reasons.append("presents outstanding features at a very smart price point")

            # Construct dynamic justification
            justification = f"This {m['brand']} model is recommended because it "
            parts = []
            
            if budget:
                if budget_type == "under":
                    if is_cheap_query:
                        parts.append(f"offers budget-friendly value at ₹{int(min_p):,} (target: under ₹{int(budget):,})")
                    else:
                        parts.append(f"fits your budget at ₹{int(min_p):,} (under ₹{int(budget):,})")
                elif budget_type == "above":
                    parts.append(f"meets your target price at ₹{int(min_p):,} (above ₹{int(budget):,})")
            else:
                parts.append(f"is currently priced at ₹{int(min_p):,}")
                
            if use_case_reasons:
                parts.append(" ".join(use_case_reasons))
            else:
                parts.append(f"boasts an impressive Smart Value Score of {m['ml_score']}/100 based on user rating ({m['avg_rating']} stars) and sentiment analysis")
                
            justification += ", ".join(parts[:2]) + "."
            
            # Append highlights if any
            if spec_highlights:
                justification += " Key Specs: " + " | ".join(spec_highlights) + "."
                
            m["justification"] = justification
            m["relevance_score"] = relevance
            ranked_models.append(m)
            
        # Sort by relevance
        ranked_models.sort(key=lambda x: x["relevance_score"], reverse=True)
        return {"results": ranked_models[:3]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
