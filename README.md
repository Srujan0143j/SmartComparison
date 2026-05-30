# SmartCompare ⚖️

A full-stack product comparison and sentiment analysis platform built with a FastAPI backend, MongoDB, and a pure-Python ML scoring model.

## Features
- **Store-Level Comparison**: Compare prices, customer ratings, and sentiments for a specific product across **Amazon**, **Flipkart**, and **Croma**.
- **Cross-Model Comparison**: Select multiple models (e.g., iPhone 15 vs. Galaxy S24) and compare specifications, ML final ratings, and prices side-by-side.
- **NLP Sentiment Analysis**: Pure-Python lexicon-based sentiment analysis processor evaluates product reviews on the fly.
- **Dynamic Charting**: Real-time rendering of radar and bar charts utilizing **Chart.js** to evaluate the Price vs. Value tradeoff.
- **MongoDB Auto-Seeder**: Automatic generation of simulated, realistic datasets for 5 categories (Smartphones, Laptops, Headphones, TVs, and Cameras) across multiple brands.
- **Resilient Fallback Mode**: If a local MongoDB instance is not detected, the backend dynamically falls back to an **in-memory mock database**, allowing the application to run instantly out-of-the-box!

---

## Technical Stack
- **Backend API**: FastAPI (Python 3.10+)
- **Database**: MongoDB (via `pymongo`)
- **Frontend**: HTML5, CSS3 (Glassmorphism design system), Vanilla JS, Chart.js
- **ML Processing**: Rule-based decision ranking engine (Normalized price, rating, reviews volume, and sentiment index).

---

## Getting Started

### 1. Launch the Backend Server
First, navigate to the `smartcompare` directory and run:

```bash
# Verify requirements are installed
python -m pip install -r backend/requirements.txt

# Start the FastAPI server on port 8000
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Once running, you can access the interactive API docs at `http://localhost:8000/docs`.

### 2. Launch the Frontend
Simply double-click or open `frontend/index.html` in your web browser. You're ready to search and compare products!

*Note: The frontend is fully configured to talk to the backend on `http://localhost:8000` via CORS.*

### 3. Setup MongoDB (Optional)
By default, if MongoDB is running locally at `mongodb://localhost:27017`, the app will automatically connect and seed a collection. If not running, it will run gracefully using the in-memory fallback!
