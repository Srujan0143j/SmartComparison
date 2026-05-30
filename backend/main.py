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
        
        # Run ML engine on results to score them
        scored_results = ml_engine.score_and_recommend(results)
        
        # Return unique grouped products (just list the models, showing their average rating & price range)
        # to prevent listing "OnePlus 12" 3 times in the general search results.
        grouped_models = {}
        for p in scored_results:
            name = p["name"]
            listing_info = {
                "source": p["source"],
                "price": p["price"],
                "url": p["url"],
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
                    "best_deal_url": p["url"],
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
                    gm["best_deal_url"] = p["url"]
                    gm["best_deal_score"] = curr_ml
                    
        return {"results": list(grouped_models.values()), "raw_count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            
        # Analyze using ML engine
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
