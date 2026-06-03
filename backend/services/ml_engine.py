import math
import re
from typing import List, Dict, Any

def analyze_sentiment(text: str) -> float:
    """A fast, rule-based lexicon sentiment analyzer in pure Python.
    Returns a score between -1.0 (very negative) and 1.0 (very positive).
    """
    POSITIVE_WORDS = {
        'great', 'excellent', 'love', 'perfect', 'awesome', 'good', 'best', 
        'super', 'amazing', 'happy', 'efficient', 'durable', 'nice', 'fast',
        'satisfied', 'outstanding', 'wonderful', 'flawless', 'recommend'
    }
    NEGATIVE_WORDS = {
        'bad', 'cheap', 'terrible', 'worst', 'broken', 'lagging', 'overheats', 
        'waste', 'disappointed', 'slow', 'fail', 'failure', 'returned', 'damage',
        'faulty', 'glitch', 'poor', 'useless', 'refund', 'regret'
    }
    
    words = text.lower().replace('.', ' ').replace(',', ' ').replace('!', ' ').split()
    if not words:
        return 0.0
        
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    
    # Simple modifiers search (e.g., 'not great')
    for i in range(1, len(words)):
        if words[i] in POSITIVE_WORDS and words[i-1] in {'not', 'no', 'never', 'dont'}:
            pos -= 1
            neg += 1
        elif words[i] in NEGATIVE_WORDS and words[i-1] in {'not', 'no', 'never', 'dont'}:
            neg -= 1
            pos += 0.5 # Double negative can imply slightly positive
            
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total

class PurePythonClassifier:
    """A pure Python Decision Forest / Rule Classifier mimicking our ML layout."""
    def predict(self, features: List[List[float]]) -> List[int]:
        results = []
        for feat in features:
            p_score, r_score, s_score, v_score = feat
            composite = 0.4 * r_score + 0.3 * s_score + 0.2 * p_score + 0.1 * v_score
            
            if p_score > 0.85 and r_score >= 0.7:
                label = 1  # Budget Pick
            elif r_score > 0.9 and p_score < 0.4 and s_score > 0.8:
                label = 2  # Premium Choice
            elif composite > 0.75:
                label = 3  # Best Value
            else:
                label = 0  # Standard
            results.append(label)
        return results

class MLEngine:
    def __init__(self):
        self.clf = PurePythonClassifier()
        print("ML Engine: Pure Python Recommendation Engine initialized successfully.")

    def extract_pros_and_cons(self, reviews: List[Dict[str, Any]], category: str) -> Dict[str, List[str]]:
        """Scans review texts to identify keyword frequencies and dynamically
        summarizes positive highlights (Pros) and negative complaints (Cons).
        """
        pros_counts = {}
        cons_counts = {}
        
        KEYWORD_PROS = {
            "battery": ("✓ Excellent Battery Backup", ["battery", "backup", "charging", "charger", "long battery"]),
            "performance": ("✓ Fast & Snappy Performance", ["fast", "speed", "performance", "smooth", "snappy", "processor"]),
            "display": ("✓ Vibrant AMOLED/OLED Screen", ["screen", "display", "oled", "brightness", "color"]),
            "camera": ("✓ Detailed & Clear Cameras", ["camera", "photo", "video", "lens", "sensor", "low light"]),
            "build": ("✓ Premium Durable Design", ["build", "premium", "design", "look", "sleek", "solid", "sturdy"]),
            "value": ("✓ Great Value for Money", ["value", "worth", "affordable", "deal", "price"])
        }
        
        KEYWORD_CONS = {
            "battery": ("✗ High Battery Drain", ["drain", "battery is low", "rapid drain", "charging is slow"]),
            "performance": ("✗ Slow Interface Lag", ["lag", "slow", "delay", "freeze", "stutter"]),
            "display": ("✗ Average Screen Brightness", ["dim screen", "dull colors", "washed out"]),
            "camera": ("✗ Grainy Low-Light Photos", ["grainy", "blurry", "camera is average", "poor low light"]),
            "build": ("✗ Slightly Bulky Form Factor", ["bulky", "heavy", "plastic", "flimsy", "fragile"]),
            "value": ("✗ Priced Premium", ["expensive", "costly", "overpriced", "priced high"]),
            "heat": ("✗ Overheating Under Load", ["heat", "hot", "overheat", "warm", "heating"])
        }
        
        for r in reviews:
            text = r.get("text", "").lower()
            sentiment = r.get("sentiment_score", 0.0)
            
            if sentiment > 0.15:
                for key, (label, words) in KEYWORD_PROS.items():
                    if any(w in text for w in words):
                        pros_counts[label] = pros_counts.get(label, 0) + 1
            elif sentiment < -0.1:
                for key, (label, words) in KEYWORD_CONS.items():
                    if any(w in text for w in words):
                        cons_counts[label] = cons_counts.get(label, 0) + 1
                        
        sorted_pros = sorted(pros_counts.keys(), key=lambda x: pros_counts[x], reverse=True)
        sorted_cons = sorted(cons_counts.keys(), key=lambda x: cons_counts[x], reverse=True)
        
        # Fallbacks to guarantee populated specs
        if not sorted_pros:
            if category == "Smartphones":
                sorted_pros = ["✓ Vibrant Glass Design", "✓ Fast Charging Support"]
            elif category == "Laptops":
                sorted_pros = ["✓ Ergonomic Keyboard", "✓ Good Port Selection"]
            else:
                sorted_pros = ["✓ Sleek Modern Build", "✓ Reliable Performance"]
                
        if not sorted_cons:
            if category == "Smartphones":
                sorted_cons = ["✗ Average Speaker Volume"]
            elif category == "Laptops":
                sorted_cons = ["✗ Trackpad feels slightly stiff"]
            else:
                sorted_cons = ["✗ Basic packaging design"]
                
        return {
            "pros": sorted_pros[:3],
            "cons": sorted_cons[:3]
        }

    def detect_fake_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run heuristics to evaluate if a review is likely fake or duplicate.
        Sets 'is_fake' and 'fake_probability' on each review dict.
        """
        if not reviews:
            return reviews
            
        text_freqs = {}
        for r in reviews:
            text = r.get("text", "").strip().lower()
            text_freqs[text] = text_freqs.get(text, 0) + 1
            
        for r in reviews:
            text = r.get("text", "").strip()
            rating = r.get("rating", 3.0) or 3.0
            sentiment = r.get("sentiment_score", 0.0) or 0.0
            
            prob = 0.0
            
            if text_freqs.get(text.lower(), 0) > 1:
                prob += 0.5
                
            words = text.split()
            if len(words) < 4:
                if rating >= 5.0 or rating <= 1.0:
                    prob += 0.4
                    
            if len(re.findall(r'!{2,}', text)) > 0:
                prob += 0.25
                
            if len(text) > 15 and text.isupper():
                prob += 0.35
                
            if rating >= 4.5 and sentiment <= -0.3:
                prob += 0.5
            elif rating <= 2.0 and sentiment >= 0.4:
                prob += 0.5
                
            r["fake_probability"] = round(min(1.0, prob), 2)
            r["is_fake"] = r["fake_probability"] >= 0.5
            
        return reviews

    def calculate_price_prediction(self, price_history: List[Dict[str, Any]], current_price: float) -> Dict[str, Any]:
        """Analyzes price history trend to predict whether user should buy now or wait."""
        if not price_history or len(price_history) < 2:
            return {
                "decision": "Buy Now",
                "confidence": 80.0,
                "reason": "Stable pricing detected with standard retail values."
            }
            
        prices = [h.get("price", current_price) for h in price_history if h.get("price") is not None]
        if not prices:
            prices = [current_price]
            
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        if avg_price > 0:
            diff_from_avg = (current_price - avg_price) / avg_price
        else:
            diff_from_avg = 0.0
            
        if current_price <= min_price * 1.01:
            confidence = min(98.0, 85.0 + abs(diff_from_avg) * 100)
            return {
                "decision": "Buy Now",
                "confidence": round(confidence, 1),
                "reason": "Price is currently at its historical lowest point. Highly recommended to buy."
            }
        elif current_price >= max_price * 0.99:
            confidence = min(95.0, 75.0 + abs(diff_from_avg) * 100)
            return {
                "decision": "Wait",
                "confidence": round(confidence, 1),
                "reason": "Expected price drop within 10 days. Avoid buying at the current peak."
            }
        elif diff_from_avg <= -0.02:
            confidence = min(90.0, 70.0 + abs(diff_from_avg) * 100)
            return {
                "decision": "Buy Now",
                "confidence": round(confidence, 1),
                "reason": f"Price is currently at a weekly low ({round(abs(diff_from_avg) * 100, 1)}% below average)."
            }
        elif diff_from_avg >= 0.02:
            confidence = min(90.0, 70.0 + diff_from_avg * 100)
            return {
                "decision": "Wait",
                "confidence": round(confidence, 1),
                "reason": f"Price is inflated by {round(diff_from_avg * 100, 1)}% from average. Wait for drop."
            }
        else:
            return {
                "decision": "Buy Now",
                "confidence": 75.0,
                "reason": "Price is stable and close to the historical weekly average."
            }

    def calculate_sentiment_for_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processes each review in every product, calculates review sentiment,
        and adds an aggregate `ml_sentiment` score to the product.
        """
        for prod in products:
            reviews = prod.get("reviews", [])
            sentiments = []
            for rev in reviews:
                score = analyze_sentiment(rev.get("text", ""))
                rev["sentiment_score"] = score
                sentiments.append(score)
            
            if sentiments:
                prod["ml_sentiment"] = float(sum(sentiments) / len(sentiments))
            else:
                rating = prod.get("rating", 3.0)
                prod["ml_sentiment"] = float((rating - 3.0) / 2.0)
        return products

    def score_and_recommend(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculates final ML scores and predicts labels using the new 40-30-20-10 weights.
        Exposes Pros/Cons, Price Predictions, and Review Trust Scores.
        """
        if not products:
            return []

        # 1. Update review sentiments & fake review flags
        products = self.calculate_sentiment_for_products(products)
        
        for p in products:
            reviews = p.get("reviews", [])
            p["reviews"] = self.detect_fake_reviews(reviews)
            
            if reviews:
                fake_count = sum(1 for r in reviews if r.get("is_fake", False))
                p["fake_review_percentage"] = round((fake_count / len(reviews)) * 100.0, 1)
            else:
                p["fake_review_percentage"] = 0.0
                
            p["review_trust_score"] = round(100.0 - p["fake_review_percentage"], 1)
            
            # Extract Pros and Cons
            summary = self.extract_pros_and_cons(reviews, p.get("category", ""))
            p["pros"] = summary["pros"]
            p["cons"] = summary["cons"]

        # 2. Extract price and review count bounds for normalization
        prices = [p.get("price") for p in products if p.get("price") is not None]
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        review_counts = [p.get("review_count", 0) or 0 for p in products]
        max_reviews = max(review_counts) if review_counts and max(review_counts) > 0 else 1

        # 3. Compute metrics for each product
        for p in products:
            price_val = p.get("price")
            if price_val is None:
                price_val = max_price
                
            # Price Score: cheaper is better
            if max_price == min_price:
                p_score = 1.0
            else:
                p_score = 1.0 - ((price_val - min_price) / (max_price - min_price))

            # Rating Score: 0 to 1
            rating_val = p.get("rating", 3.0)
            if rating_val is None:
                rating_val = 3.0
            r_score = rating_val / 5.0

            # Sentiment Score: map [-1, 1] to [0, 1]
            s_score = (p.get("ml_sentiment", 0.0) + 1.0) / 2.0

            # Review Volume Score (logarithmic scaling)
            rev_count = p.get("review_count", 1)
            if rev_count is None or rev_count < 1:
                rev_count = 1
            v_score = math.log(rev_count) / math.log(max_reviews) if max_reviews > 1 else 1.0

            # Weighted Formula: 40% Rating, 30% Sentiment, 20% Price, 10% Volume
            composite_score = (0.4 * r_score + 0.3 * s_score + 0.2 * p_score + 0.1 * v_score) * 100
            p["ml_score"] = round(composite_score, 1)
            p["best_value_score"] = p["ml_score"]

            # Predict Label
            features = [[p_score, r_score, s_score, v_score]]
            pred_class = self.clf.predict(features)[0]
            
            label_map = {
                1: "Budget Pick",
                2: "Premium Choice",
                3: "Best Value",
                0: "Recommended"
            }
            p["ml_label"] = label_map.get(pred_class, "Recommended")
            p["price_prediction"] = self.calculate_price_prediction(p.get("price_history", []), price_val)

        # Sort products by ML Score descending
        sorted_by_score = sorted(products, key=lambda x: x["ml_score"], reverse=True)
        if sorted_by_score:
            sorted_by_score[0]["ml_label"] = "Best Value"
            
        sorted_by_price = sorted(products, key=lambda x: x.get("price") if x.get("price") is not None else float('inf'))
        if sorted_by_price and len(products) > 1:
            cheapest = sorted_by_price[0]
            cheapest_price = cheapest.get("price")
            cheapest_rating = cheapest.get("rating", 0.0) or 0.0
            cheapest_label = cheapest.get("ml_label")
            if cheapest_price is not None and cheapest_rating >= 3.5 and cheapest_label != "Best Value":
                cheapest["ml_label"] = "Budget Pick"

        return products

ml_engine = MLEngine()
