from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Review(BaseModel):
    author: Optional[str] = "Anonymous"
    rating: Optional[float] = None
    title: Optional[str] = ""
    text: str
    sentiment_score: Optional[float] = None
    is_fake: Optional[bool] = False
    fake_probability: Optional[float] = 0.0

class Product(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    category: str
    brand: str
    price: float
    currency: str = "INR"
    source: str  # Amazon, Flipkart, Croma, etc.
    url: str
    image_url: str
    rating: float
    review_count: int
    reviews: List[Review] = []
    specifications: Dict[str, Any] = {}
    
    # ML Outputs & Price Tracking
    ml_score: Optional[float] = None
    ml_sentiment: Optional[float] = None
    ml_label: Optional[str] = None
    best_value_score: Optional[float] = None
    fake_review_percentage: Optional[float] = 0.0
    review_trust_score: float = 100.0
    pros: List[str] = []
    cons: List[str] = []
    price_history: List[Dict[str, Any]] = []  # list of {"date": "YYYY-MM-DD", "price": float}
    price_prediction: Optional[Dict[str, Any]] = {}  # {"decision": "Buy Now"/"Wait", "confidence": float, "reason": str}

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "OnePlus 12 5G",
                "category": "Smartphones",
                "brand": "OnePlus",
                "price": 64999.00,
                "currency": "INR",
                "source": "Amazon",
                "url": "https://amazon.in/...",
                "image_url": "https://...",
                "rating": 4.5,
                "review_count": 1250,
                "reviews": [
                    {"author": "Amit", "rating": 5, "title": "Excellent phone", "text": "Super performance and awesome battery life.", "is_fake": False, "fake_probability": 0.05}
                ],
                "specifications": {
                    "RAM": "16 GB",
                    "Storage": "512 GB",
                    "Processor": "Snapdragon 8 Gen 3"
                },
                "best_value_score": 92.5,
                "fake_review_percentage": 0.0,
                "review_trust_score": 100.0,
                "pros": ["Excellent battery backup", "Stunning design", "Very fast processor"],
                "cons": ["Slightly expensive", "No charger in box"],
                "price_history": [
                    {"date": "2026-05-27", "price": 65500.0},
                    {"date": "2026-05-28", "price": 65200.0},
                    {"date": "2026-05-29", "price": 64999.0}
                ],
                "price_prediction": {
                    "decision": "Buy Now",
                    "confidence": 88.0,
                    "reason": "Price is at a weekly low."
                }
            }
        }
