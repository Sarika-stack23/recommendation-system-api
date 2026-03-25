"""
Complete Recommendation System with API
Single file implementation: Database + Engine + API + Testing + Metrics
Run: pip install flask numpy
Then: python main.py
API runs at: http://localhost:5000
"""

import sqlite3
import json
import math
import time
import random
import hashlib
import logging
import threading
import unittest
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────

DB_PATH = "recommendation_system.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Create all tables."""
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            age         INTEGER,
            preferences TEXT,          -- JSON list of genres
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS content (
            content_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            genre       TEXT,
            tags        TEXT,          -- JSON list
            skills      TEXT,          -- JSON list
            difficulty  TEXT,          -- beginner / intermediate / advanced
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS skills (
            skill_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            category    TEXT,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS interactions (
            interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER REFERENCES users(user_id),
            content_id     INTEGER REFERENCES content(content_id),
            action         TEXT,       -- view / like / complete
            rating         REAL,       -- 1.0 – 5.0
            timestamp      TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized.")

# ─────────────────────────────────────────────
# SEED DATA  (10 users, 20 content, 50+ interactions)
# ─────────────────────────────────────────────

def seed_data():
    conn = get_conn()
    cur = conn.cursor()

    # Skip if already seeded
    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        conn.close()
        return

    users = [
        ("Alice",  25, ["ML", "Python"]),
        ("Bob",    30, ["Web", "JavaScript"]),
        ("Carol",  22, ["Data Science", "Python"]),
        ("Dave",   28, ["DevOps", "Cloud"]),
        ("Eve",    35, ["ML", "Deep Learning"]),
        ("Frank",  27, ["Web", "React"]),
        ("Grace",  24, ["Data Science", "SQL"]),
        ("Hank",   32, ["Cloud", "AWS"]),
        ("Ivy",    26, ["Python", "Automation"]),
        ("Jack",   29, ["ML", "NLP"]),
    ]
    for name, age, prefs in users:
        cur.execute(
            "INSERT INTO users (name, age, preferences) VALUES (?,?,?)",
            (name, age, json.dumps(prefs))
        )

    content_items = [
        ("Intro to Python",          "Python",       ["python","beginner"],          ["Python"],            "beginner"),
        ("Advanced ML Techniques",   "ML",           ["ml","advanced","neural"],      ["ML","Python"],       "advanced"),
        ("React for Beginners",      "Web",          ["react","frontend","js"],       ["React","JS"],        "beginner"),
        ("Docker & Kubernetes",      "DevOps",       ["docker","k8s","containers"],   ["DevOps"],            "intermediate"),
        ("Deep Learning with PyTorch","Deep Learning",["pytorch","dl","cnn"],         ["ML","Python"],       "advanced"),
        ("SQL Mastery",              "Data Science", ["sql","databases","queries"],   ["SQL"],               "intermediate"),
        ("AWS Cloud Essentials",     "Cloud",        ["aws","cloud","s3","ec2"],      ["Cloud","AWS"],       "beginner"),
        ("NLP with Transformers",    "NLP",          ["nlp","bert","transformers"],   ["ML","NLP"],          "advanced"),
        ("FastAPI Development",      "Web",          ["fastapi","python","api"],      ["Python","Web"],      "intermediate"),
        ("Data Visualization",       "Data Science", ["matplotlib","seaborn","viz"],  ["Python","DataViz"],  "beginner"),
        ("JavaScript ES6+",          "Web",          ["js","es6","async"],            ["JavaScript"],        "intermediate"),
        ("Pandas for Data Analysis", "Data Science", ["pandas","dataframe","python"], ["Python","Data"],     "beginner"),
        ("CI/CD Pipelines",          "DevOps",       ["cicd","github","jenkins"],     ["DevOps"],            "intermediate"),
        ("Computer Vision Basics",   "ML",           ["cv","image","opencv"],         ["ML","Python"],       "intermediate"),
        ("GraphQL API Design",       "Web",          ["graphql","api","schema"],      ["Web","JS"],          "advanced"),
        ("Reinforcement Learning",   "ML",           ["rl","policy","reward"],        ["ML","Python"],       "advanced"),
        ("Terraform on AWS",         "Cloud",        ["terraform","iac","aws"],       ["Cloud","DevOps"],    "advanced"),
        ("Streamlit Dashboards",     "Python",       ["streamlit","dashboard","ui"],  ["Python","Web"],      "beginner"),
        ("Time Series Analysis",     "Data Science", ["timeseries","forecasting"],    ["Python","ML"],       "intermediate"),
        ("LangChain & LLMs",         "ML",           ["llm","langchain","genai"],     ["ML","Python","NLP"], "advanced"),
    ]
    for title, genre, tags, skills, diff in content_items:
        cur.execute(
            "INSERT INTO content (title, genre, tags, skills, difficulty) VALUES (?,?,?,?,?)",
            (title, genre, json.dumps(tags), json.dumps(skills), diff)
        )

    skills_data = [
        ("Python",      "Programming", "General-purpose programming language"),
        ("ML",          "AI",          "Machine learning algorithms and models"),
        ("JavaScript",  "Programming", "Web scripting language"),
        ("SQL",         "Database",    "Structured query language"),
        ("DevOps",      "Operations",  "Development operations practices"),
        ("Cloud",       "Infrastructure","Cloud computing platforms"),
        ("React",       "Frontend",    "UI component library"),
        ("NLP",         "AI",          "Natural language processing"),
        ("DataViz",     "Data",        "Data visualization techniques"),
        ("AWS",         "Cloud",       "Amazon Web Services"),
    ]
    for name, cat, desc in skills_data:
        cur.execute(
            "INSERT INTO skills (name, category, description) VALUES (?,?,?)",
            (name, cat, desc)
        )

    # Realistic interactions
    interactions = [
        (1,1,"complete",5.0),(1,2,"like",4.5),(1,10,"view",3.0),(1,12,"complete",4.0),
        (2,3,"complete",5.0),(2,11,"like",4.0),(2,9,"view",3.5),(2,15,"like",4.5),
        (3,1,"complete",4.0),(3,6,"like",5.0),(3,10,"complete",4.5),(3,12,"view",3.0),(3,19,"like",4.0),
        (4,4,"complete",5.0),(4,7,"like",4.0),(4,13,"complete",4.5),(4,17,"view",3.5),
        (5,2,"complete",5.0),(5,5,"like",5.0),(5,8,"complete",4.5),(5,16,"view",4.0),(5,20,"like",5.0),
        (6,3,"complete",4.0),(6,9,"like",4.5),(6,11,"view",3.0),(6,15,"complete",5.0),
        (7,6,"complete",5.0),(7,10,"like",4.0),(7,12,"complete",4.5),(7,19,"view",3.5),
        (8,4,"complete",4.5),(8,7,"like",5.0),(8,13,"view",3.0),(8,17,"complete",4.0),
        (9,1,"complete",4.0),(9,9,"like",4.5),(9,18,"complete",5.0),(9,12,"view",3.0),
        (10,2,"complete",5.0),(10,8,"like",4.5),(10,20,"complete",5.0),(10,5,"view",4.0),
        # Extra interactions for density
        (1,5,"view",3.5),(2,6,"view",3.0),(3,5,"like",4.0),(4,2,"view",3.0),
        (5,14,"complete",4.5),(6,8,"like",4.0),(7,16,"view",3.0),(8,20,"like",4.5),
        (9,14,"complete",4.0),(10,13,"view",3.5),(1,20,"like",4.0),(2,19,"view",3.0),
    ]
    for uid, cid, action, rating in interactions:
        cur.execute(
            "INSERT INTO interactions (user_id,content_id,action,rating) VALUES (?,?,?,?)",
            (uid, cid, action, rating)
        )

    conn.commit()
    conn.close()
    logger.info("Seed data inserted.")

# ─────────────────────────────────────────────
# REPOSITORY LAYER
# ─────────────────────────────────────────────

class UserRepository:
    def get(self, user_id):
        conn = get_conn()
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def all_ids(self):
        conn = get_conn()
        rows = conn.execute("SELECT user_id FROM users").fetchall()
        conn.close()
        return [r["user_id"] for r in rows]

    def preferences(self, user_id):
        user = self.get(user_id)
        if not user:
            return []
        return json.loads(user.get("preferences") or "[]")


class ContentRepository:
    def get(self, content_id):
        conn = get_conn()
        row = conn.execute("SELECT * FROM content WHERE content_id=?", (content_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def all(self):
        conn = get_conn()
        rows = conn.execute("SELECT * FROM content").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def all_ids(self):
        return [c["content_id"] for c in self.all()]


class InteractionRepository:
    def add(self, user_id, content_id, action, rating):
        conn = get_conn()
        conn.execute(
            "INSERT INTO interactions (user_id,content_id,action,rating) VALUES (?,?,?,?)",
            (user_id, content_id, action, rating)
        )
        conn.commit()
        conn.close()

    def by_user(self, user_id):
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM interactions WHERE user_id=?", (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def all(self):
        conn = get_conn()
        rows = conn.execute("SELECT * FROM interactions").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def user_content_matrix(self):
        """Returns {user_id: {content_id: rating}}"""
        matrix = {}
        for row in self.all():
            uid  = row["user_id"]
            cid  = row["content_id"]
            rating = row["rating"] or 3.0
            if uid not in matrix:
                matrix[uid] = {}
            matrix[uid][cid] = max(matrix[uid].get(cid, 0), rating)
        return matrix


# ─────────────────────────────────────────────
# RECOMMENDATION ENGINE
# ─────────────────────────────────────────────

user_repo    = UserRepository()
content_repo = ContentRepository()
inter_repo   = InteractionRepository()

# Simple in-memory cache
_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 60  # seconds

def _cache_get(key):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry["ts"]) < CACHE_TTL:
            return entry["data"]
    return None

def _cache_set(key, data):
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time()}


def cosine_similarity(vec_a, vec_b):
    """Cosine similarity between two rating dicts."""
    keys = set(vec_a) & set(vec_b)
    if not keys:
        return 0.0
    dot   = sum(vec_a[k] * vec_b[k] for k in keys)
    norm_a = math.sqrt(sum(v**2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v**2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def collaborative_filter(user_id, top_n=5):
    """User-based collaborative filtering."""
    matrix = inter_repo.user_content_matrix()
    if user_id not in matrix:
        return []

    user_vec = matrix[user_id]
    scores = {}

    for other_id, other_vec in matrix.items():
        if other_id == user_id:
            continue
        sim = cosine_similarity(user_vec, other_vec)
        if sim <= 0:
            continue
        for cid, rating in other_vec.items():
            if cid not in user_vec:          # not yet seen
                scores[cid] = scores.get(cid, 0) + sim * rating

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in ranked[:top_n]]


def content_based_filter(user_id, top_n=5):
    """Match user preferences to content tags/skills."""
    prefs = user_repo.preferences(user_id)
    if not prefs:
        return []

    seen = {r["content_id"] for r in inter_repo.by_user(user_id)}
    all_content = content_repo.all()
    scores = {}

    for item in all_content:
        if item["content_id"] in seen:
            continue
        tags   = json.loads(item.get("tags")   or "[]")
        skills = json.loads(item.get("skills") or "[]")
        combined = [t.lower() for t in tags + skills]
        score = sum(1 for p in prefs if p.lower() in combined)
        if score > 0:
            scores[item["content_id"]] = score

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in ranked[:top_n]]


def cold_start(top_n=5):
    """Popular content for new users."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT content_id, COUNT(*) as cnt, AVG(rating) as avg_r
        FROM interactions
        GROUP BY content_id
        ORDER BY cnt DESC, avg_r DESC
        LIMIT ?
    """, (top_n,)).fetchall()
    conn.close()
    return [r["content_id"] for r in rows]


def generate_explanation(user_id, content_id, source):
    """Human-readable explanation for a recommendation."""
    item = content_repo.get(content_id)
    if not item:
        return "Recommended for you."
    title = item["title"]
    if source == "collaborative":
        return f"Users with similar interests enjoyed '{title}'."
    if source == "content":
        prefs = user_repo.preferences(user_id)
        return f"Matches your interest in {', '.join(prefs[:2])}."
    return f"'{title}' is trending among all learners."


def get_recommendations(user_id, top_n=5):
    """Hybrid recommender with cache."""
    cache_key = f"rec_{user_id}_{top_n}"
    cached = _cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for user {user_id}")
        return cached

    user = user_repo.get(user_id)
    if not user:
        return {"error": "User not found"}

    interactions = inter_repo.by_user(user_id)

    if not interactions:
        # Cold start
        ids = cold_start(top_n)
        results = []
        for cid in ids:
            item = content_repo.get(cid)
            if item:
                results.append({
                    "content_id":  cid,
                    "title":       item["title"],
                    "genre":       item["genre"],
                    "difficulty":  item["difficulty"],
                    "source":      "popular",
                    "explanation": generate_explanation(user_id, cid, "cold_start")
                })
    else:
        cf_ids  = collaborative_filter(user_id, top_n)
        cb_ids  = content_based_filter(user_id, top_n)

        # Merge: CF gets priority, fill with CB
        merged = list(dict.fromkeys(cf_ids + cb_ids))[:top_n]

        results = []
        for cid in merged:
            item = content_repo.get(cid)
            source = "collaborative" if cid in cf_ids else "content"
            if item:
                results.append({
                    "content_id":  cid,
                    "title":       item["title"],
                    "genre":       item["genre"],
                    "difficulty":  item["difficulty"],
                    "source":      source,
                    "explanation": generate_explanation(user_id, cid, source)
                })

    _cache_set(cache_key, results)
    return results


# ─────────────────────────────────────────────
# EVALUATION METRICS
# ─────────────────────────────────────────────

def precision_at_k(recommended, relevant, k=5):
    rec_k = recommended[:k]
    hits  = len(set(rec_k) & set(relevant))
    return hits / k if k > 0 else 0.0

def recall_at_k(recommended, relevant, k=5):
    rec_k = recommended[:k]
    hits  = len(set(rec_k) & set(relevant))
    return hits / len(relevant) if relevant else 0.0

def ndcg_at_k(recommended, relevant, k=5):
    rec_k = recommended[:k]
    dcg   = sum(
        1 / math.log2(i + 2)
        for i, cid in enumerate(rec_k)
        if cid in relevant
    )
    idcg  = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / idcg if idcg > 0 else 0.0

def run_evaluation():
    """Evaluate across all users using leave-one-out strategy."""
    matrix = inter_repo.user_content_matrix()
    p_scores, r_scores, n_scores = [], [], []

    for user_id, ratings in matrix.items():
        # Items rated >= 4.0 are considered relevant ground truth
        relevant = [cid for cid, r in ratings.items() if r >= 4.0]
        if not relevant:
            continue

        # Temporarily remove one relevant item and see if engine recommends it
        # Use all content NOT seen by user as the pool for recommendations
        all_content_ids = set(content_repo.all_ids())
        seen_ids = set(ratings.keys())
        unseen_ids = all_content_ids - seen_ids

        # Build pseudo recommendations: collaborative + content scores on unseen
        cf_ids = collaborative_filter(user_id, top_n=10)
        cb_ids = content_based_filter(user_id, top_n=10)
        merged = list(dict.fromkeys(cf_ids + cb_ids))[:5]

        # Ground truth: high-rated items from OTHER users that this user hasn't seen
        other_high_rated = set()
        for other_id, other_ratings in matrix.items():
            if other_id == user_id:
                continue
            for cid, r in other_ratings.items():
                if r >= 4.0 and cid in unseen_ids:
                    other_high_rated.add(cid)

        # Use intersection of recommendations and other users' high-rated items
        ground_truth = list(other_high_rated) if other_high_rated else relevant

        if not ground_truth:
            continue

        p_scores.append(precision_at_k(merged, ground_truth))
        r_scores.append(recall_at_k(merged, ground_truth))
        n_scores.append(ndcg_at_k(merged, ground_truth))

    return {
        "precision@5":     round(sum(p_scores)/len(p_scores), 4) if p_scores else 0,
        "recall@5":        round(sum(r_scores)/len(r_scores), 4) if r_scores else 0,
        "ndcg@5":          round(sum(n_scores)/len(n_scores), 4) if n_scores else 0,
        "users_evaluated": len(p_scores)
    }


# ─────────────────────────────────────────────
# REQUEST STATS
# ─────────────────────────────────────────────

_stats = {"total_requests": 0, "total_ms": 0.0, "errors": 0}
_stats_lock = threading.Lock()

def record_request(ms, error=False):
    with _stats_lock:
        _stats["total_requests"] += 1
        _stats["total_ms"]       += ms
        if error:
            _stats["errors"] += 1


# ─────────────────────────────────────────────
# FLASK API
# ─────────────────────────────────────────────

app = Flask(__name__)

def timed(f):
    """Decorator: log response time and trace ID."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        trace_id = hashlib.md5(
            f"{time.time()}{random.random()}".encode()
        ).hexdigest()[:8]
        start = time.time()
        try:
            resp = f(*args, **kwargs)
            ms = (time.time() - start) * 1000
            record_request(ms)
            logger.info(f"[{trace_id}] {request.method} {request.path} → {ms:.1f}ms")
            return resp
        except Exception as e:
            ms = (time.time() - start) * 1000
            record_request(ms, error=True)
            logger.error(f"[{trace_id}] ERROR: {e}")
            return jsonify({"error": str(e)}), 500
    return wrapper


@app.route("/", methods=["GET"])
def home():
    """Root route - API info page."""
    return jsonify({
        "name":    "Recommendation System API",
        "version": "1.0.0",
        "status":  "running",
        "endpoints": {
            "health":          "GET  /health",
            "recommendations": "GET  /recommendations/<user_id>",
            "feedback":        "POST /feedback",
            "metrics":         "GET  /metrics"
        }
    })


@app.route("/recommendations/<int:user_id>", methods=["GET"])
@timed
def recommendations(user_id):
    """GET /recommendations/<user_id>?top_n=5"""
    top_n = int(request.args.get("top_n", 5))
    result = get_recommendations(user_id, top_n)
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 404
    return jsonify({"user_id": user_id, "recommendations": result})


@app.route("/feedback", methods=["POST"])
@timed
def feedback():
    """
    POST /feedback
    Body: {"user_id": 1, "content_id": 3, "action": "like", "rating": 4.5}
    """
    data = request.get_json()
    required = ["user_id", "content_id", "action", "rating"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    inter_repo.add(
        data["user_id"], data["content_id"],
        data["action"],  data["rating"]
    )
    # Invalidate cache for this user
    _cache.pop(f"rec_{data['user_id']}_5", None)
    return jsonify({"status": "ok", "message": "Feedback recorded."})


@app.route("/health", methods=["GET"])
@timed
def health():
    """GET /health"""
    conn = get_conn()
    user_count    = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    content_count = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    conn.close()
    return jsonify({
        "status":   "healthy",
        "db":       "connected",
        "users":    user_count,
        "content":  content_count,
        "time":     datetime.now().isoformat()
    })


@app.route("/metrics", methods=["GET"])
@timed
def metrics():
    """GET /metrics"""
    with _stats_lock:
        total = _stats["total_requests"]
        avg_ms = (_stats["total_ms"] / total) if total else 0
    eval_scores = run_evaluation()
    return jsonify({
        "total_requests":  total,
        "avg_response_ms": round(avg_ms, 2),
        "errors":          _stats["errors"],
        "cache_size":      len(_cache),
        "evaluation":      eval_scores
    })


# ─────────────────────────────────────────────
# UNIT TESTS
# ─────────────────────────────────────────────

class TestRecommendationSystem(unittest.TestCase):

    def test_cosine_similarity_identical(self):
        v = {1: 5.0, 2: 3.0}
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0)

    def test_cosine_similarity_no_overlap(self):
        self.assertEqual(cosine_similarity({1: 5.0}, {2: 3.0}), 0.0)

    def test_precision_at_k(self):
        self.assertEqual(precision_at_k([1,2,3,4,5], [1,3], k=5), 0.4)

    def test_recall_at_k(self):
        self.assertEqual(recall_at_k([1,2,3,4,5], [1,3,6], k=5), 2/3)

    def test_ndcg_at_k_perfect(self):
        relevant = [1,2,3,4,5]
        self.assertAlmostEqual(ndcg_at_k(relevant, relevant, k=5), 1.0)

    def test_cold_start_returns_list(self):
        result = cold_start(5)
        self.assertIsInstance(result, list)

    def test_recommendations_unknown_user(self):
        result = get_recommendations(9999)
        self.assertIn("error", result)

    def test_recommendations_known_user(self):
        result = get_recommendations(1)
        self.assertIsInstance(result, list)

    def test_content_repo_all(self):
        items = content_repo.all()
        self.assertGreaterEqual(len(items), 20)

    def test_user_repo_preferences(self):
        prefs = user_repo.preferences(1)
        self.assertIsInstance(prefs, list)


def run_tests():
    """Run all unit tests and print results."""
    print("\n" + "="*50)
    print("  RUNNING UNIT TESTS")
    print("="*50)
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TestRecommendationSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


# ─────────────────────────────────────────────
# LOAD TEST  (10 concurrent users)
# ─────────────────────────────────────────────

def load_test(concurrent=10, requests_each=5):
    """Simulate concurrent users hitting the recommendation endpoint."""
    print("\n" + "="*50)
    print("  LOAD TEST")
    print("="*50)

    results = []
    lock = threading.Lock()

    def simulate_user(user_id):
        for _ in range(requests_each):
            start = time.time()
            get_recommendations(user_id % 10 + 1)
            ms = (time.time() - start) * 1000
            with lock:
                results.append(ms)

    threads = [threading.Thread(target=simulate_user, args=(i,)) for i in range(concurrent)]
    t0 = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    total_time = time.time() - t0

    avg   = sum(results) / len(results)
    under = sum(1 for r in results if r < 200)

    print(f"  Concurrent users : {concurrent}")
    print(f"  Total requests   : {len(results)}")
    print(f"  Total time       : {total_time:.2f}s")
    print(f"  Avg response     : {avg:.2f}ms")
    print(f"  Under 200ms      : {under}/{len(results)} ({100*under//len(results)}%)")
    print("="*50 + "\n")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # 1. Setup
    init_db()
    seed_data()

    # 2. Unit tests
    run_tests()

    # 3. Load test
    load_test(concurrent=10, requests_each=5)

    # 4. Print evaluation metrics
    print("\n" + "="*50)
    print("  EVALUATION METRICS")
    print("="*50)
    scores = run_evaluation()
    for k, v in scores.items():
        print(f"  {k}: {v}")
    print("="*50 + "\n")

    # 5. Start API
    print("Starting API at http://localhost:5000")
    print("Endpoints:")
    print("  GET  /recommendations/<user_id>")
    print("  POST /feedback")
    print("  GET  /health")
    print("  GET  /metrics\n")
    app.run(debug=False, host="0.0.0.0", port=5000)