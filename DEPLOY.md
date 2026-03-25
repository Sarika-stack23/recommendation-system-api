# 🚀 Deployment Guide

Three ways to deploy your Recommendation System API.

---

## Option 1: Deploy on Render (Free & Easiest)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/your-username/recommendation-system-api.git
git push -u origin main
```

### Step 2: Create Render account
- Go to https://render.com and sign up (free)

### Step 3: Create a Web Service
1. Click **New → Web Service**
2. Connect your GitHub repo
3. Fill in these settings:

| Field | Value |
|---|---|
| Name | recommendation-system-api |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python main.py` |
| Instance Type | Free |

### Step 4: Deploy
- Click **Create Web Service**
- Wait ~2 minutes for build
- Your API is live at: `https://recommendation-system-api.onrender.com`

---

## Option 2: Deploy on Railway (Free Tier)

### Step 1: Push to GitHub (same as above)

### Step 2: Go to Railway
- Visit https://railway.app and sign in with GitHub

### Step 3: New Project
1. Click **New Project → Deploy from GitHub repo**
2. Select your repository
3. Railway auto-detects Python

### Step 4: Set Start Command
- Go to Settings → Deploy
- Set start command: `python main.py`

### Step 5: Done
- Click **Deploy** — live in ~1 minute

---

## Option 3: Deploy on Your Own VPS (Ubuntu)

### Step 1: SSH into your server
```bash
ssh user@your-server-ip
```

### Step 2: Install Python & Git
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

### Step 3: Clone your repo
```bash
git clone https://github.com/your-username/recommendation-system-api.git
cd recommendation-system-api
```

### Step 4: Setup virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 5: Run with Gunicorn (production server)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "main:app"
```

### Step 6: Keep it running with systemd
```bash
sudo nano /etc/systemd/system/recsys.service
```
Paste this:
```ini
[Unit]
Description=Recommendation System API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/recommendation-system-api
ExecStart=/home/ubuntu/recommendation-system-api/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl daemon-reload
sudo systemctl start recsys
sudo systemctl enable recsys
```

---

## ✅ Post-Deployment Checklist

- [ ] `GET /health` returns `"status": "healthy"`
- [ ] `GET /recommendations/1` returns a list
- [ ] `POST /feedback` returns `"status": "ok"`
- [ ] `GET /metrics` returns evaluation scores
- [ ] Response time under 200ms

---

## 🔒 Production Tips

1. **Disable debug mode** — already off in `main.py`
2. **Use environment variables** for any secrets
3. **Add HTTPS** — Render/Railway do this automatically
4. **Monitor logs** — use Render/Railway dashboard or `journalctl -u recsys`