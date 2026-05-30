from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Review(BaseModel):
    author: Optional[str] = "Anonymous"
    rating: Optional[float] = None
    title: Optional[str] = ""
    text: str
    sentiment_score: Optional[float] = None

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
    
    # ML Outputs
    ml_score: Optional[float] = None
    ml_sentiment: Optional[float] = None
    ml_label: Optional[str] = None

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
                    {"author": "Amit", "rating": 5, "title": "Excellent phone", "text": "Super performance and awesome battery life."}
                ],
                "specifications": {
                    "RAM": "16 GB",
                    "Storage": "512 GB",
                    "Processor": "Snapdragon 8 Gen 3"
                }
            }
        }
