import math
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
            composite = 0.3 * r_score + 0.25 * s_score + 0.25 * p_score + 0.2 * v_score
            
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
            
            # Overall product sentiment is average review sentiment
            if sentiments:
                prod["ml_sentiment"] = float(sum(sentiments) / len(sentiments))
            else:
                # Fallback mapping: ratings 1-5 to sentiment range [-0.5, 1.0]
                rating = prod.get("rating", 3.0)
                prod["ml_sentiment"] = float((rating - 3.0) / 2.0)
        return products

    def score_and_recommend(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculates final ML scores and predicts labels (Best Value, Premium Pick, Budget Pick, Recommended)
        using the rule classifier.
        """
        if not products:
            return []

        # 1. Update review sentiments
        products = self.calculate_sentiment_for_products(products)

        # 2. Extract price and review count bounds for normalization
        prices = [p.get("price") for p in products if p.get("price") is not None]
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        review_counts = [p.get("review_count", 0) or 0 for p in products]
        max_reviews = max(review_counts) if review_counts and max(review_counts) > 0 else 1

        # 3. Compute metrics for each product
        for p in products:
            # Handle potentially missing or None price
            price_val = p.get("price")
            if price_val is None:
                price_val = max_price  # Treat as maximum (least preferred) if missing
                
            # Price Score: cheaper is better (1.0 = cheapest, 0.0 = most expensive if range exists)
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

            # Composite weighted score (out of 100)
            composite_score = (0.3 * r_score + 0.25 * s_score + 0.25 * p_score + 0.2 * v_score) * 100
            p["ml_score"] = round(composite_score, 1)

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

        # Sort products by ML Score descending
        sorted_by_score = sorted(products, key=lambda x: x["ml_score"], reverse=True)
        if sorted_by_score:
            sorted_by_score[0]["ml_label"] = "Best Value"
            
        # Guarantee that cheapest gets "Budget Pick" if it is significantly cheaper and has acceptable rating
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
