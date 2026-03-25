# 🎯 Recommendation System API

A production-ready recommendation system microservice with REST API, SQLite database, hybrid recommendation engine, caching, unit tests, and evaluation metrics — all in a single file.

---

## 🚀 Features

- ✅ SQLite database with 4 normalized tables
- ✅ Hybrid recommendation engine (Collaborative + Content-Based filtering)
- ✅ Cold start handling for new users
- ✅ In-memory caching (60s TTL)
- ✅ REST API with 4 endpoints (Flask)
- ✅ Evaluation metrics: Precision@5, Recall@5, NDCG@5
- ✅ Unit tests (10 test cases, 80%+ coverage)
- ✅ Load testing (10 concurrent users)
- ✅ Request logging with trace IDs

---

## 📁 Project Structure

```
recommendation-system-api/
├── main.py            # Complete system (DB + Engine + API + Tests)
├── requirements.txt   # Dependencies
└── README.md          # Documentation
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/recommendation-system-api.git
cd recommendation-system-api
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python main.py
```

On startup, the system will:
1. 🗄️ Create SQLite database and all tables
2. 🌱 Seed 10 users, 20 content items, 50+ interactions
3. 🧪 Run all unit tests
4. ⚡ Run load test with 10 concurrent users
5. 📊 Print evaluation metrics
6. 🌐 Start Flask API at `http://localhost:5000`

---

## 🌐 API Endpoints

### 1. Get Recommendations
```
GET /recommendations/<user_id>?top_n=5
```
**Example:**
```bash
curl http://localhost:5000/recommendations/1
```
**Response:**
```json
{
  "user_id": 1,
  "recommendations": [
    {
      "content_id": 5,
      "title": "Deep Learning with PyTorch",
      "genre": "Deep Learning",
      "difficulty": "advanced",
      "source": "collaborative",
      "explanation": "Users with similar interests enjoyed 'Deep Learning with PyTorch'."
    }
  ]
}
```

---

### 2. Submit Feedback
```
POST /feedback
```
**Body:**
```json
{
  "user_id": 1,
  "content_id": 5,
  "action": "like",
  "rating": 4.5
}
```
**Example:**
```bash
curl -X POST http://localhost:5000/feedback \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"content_id":5,"action":"like","rating":4.5}'
```

---

### 3. Health Check
```
GET /health
```
**Example:**
```bash
curl http://localhost:5000/health
```
**Response:**
```json
{
  "status": "healthy",
  "db": "connected",
  "users": 10,
  "content": 20,
  "time": "2024-01-01T00:00:00"
}
```

---

### 4. Metrics
```
GET /metrics
```
**Example:**
```bash
curl http://localhost:5000/metrics
```
**Response:**
```json
{
  "total_requests": 42,
  "avg_response_ms": 12.5,
  "errors": 0,
  "cache_size": 10,
  "evaluation": {
    "precision@5": 0.42,
    "recall@5": 0.38,
    "ndcg@5": 0.45,
    "users_evaluated": 10
  }
}
```

---

## 📊 Evaluation Metrics

| Metric | Description |
|---|---|
| Precision@5 | Of top 5 recommendations, how many were relevant |
| Recall@5 | Of all relevant items, how many appeared in top 5 |
| NDCG@5 | Ranking quality of top 5 results |

---

## 🧪 Running Tests Only

```bash
python -c "
from main import *
init_db(); seed_data()
run_tests()
"
```

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.8+ |
| Database | SQLite |
| API Framework | Flask |
| Recommendation | Custom (Collaborative + Content-Based) |
| Caching | In-memory (Thread-safe) |
| Testing | unittest |

---

## 👤 Author

Built as part of HiDevs 100-Day Internship Program.

---

## 📄 License

MIT License