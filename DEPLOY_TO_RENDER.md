# 🚀 Deploy Lemon Button Cafe to Render (Free, ~5 minutes)

You'll get a permanent public link like `https://lemon-button-cafe.onrender.com`
that works on any phone. **No credit card required.**

---

## Option A — Easiest: GitHub + Render (recommended)

### 1. Create a GitHub account (skip if you have one)
- Go to https://github.com → Sign up (free)

### 2. Create a new repository
- Click **"+" (top-right)** → **"New repository"**
- Name it: `lemon-button-cafe`
- Set it to **Public**
- Click **"Create repository"**

### 3. Upload the project files
- On the empty repo page, click **"uploading an existing file"**
- Drag & drop ALL these files from the unzipped folder:
  - `app.py`
  - `requirements.txt`
  - `Procfile`
  - `runtime.txt`
  - `render.yaml`
  - `README.md`
- Click **"Commit changes"**

### 4. Deploy on Render
- Go to https://render.com → **Sign up with GitHub** (free, no credit card)
- Once logged in, click **"New +"** → **"Web Service"**
- Click **"Connect a repository"** → choose `lemon-button-cafe`
- Render auto-detects everything from `render.yaml`. You just click:
  - Instance Type: **Free**
  - Click **"Create Web Service"**
- Wait ~2 minutes while it builds. When status shows **"Live"**, you'll see your URL at the top, e.g.:
  ```
  https://lemon-button-cafe.onrender.com
  ```

### 5. Share with your family 🎉
- Customer menu: `https://YOUR-URL.onrender.com/`
- Your admin dashboard: `https://YOUR-URL.onrender.com/admin`

---

## ⚠️ Two things to know about Render's free tier

1. **Sleeps after 15 min of no traffic.** First visit after that takes ~30 seconds
   to wake up. Fine for family use. To keep it always-on, upgrade to $7/mo.

2. **Database resets on redeploy.** The free tier has no persistent disk, so if
   Render redeploys the app the `orders.db` file is wiped. For a family cafe menu
   this is usually fine (export CSV daily from `/api/orders.csv`). If you need
   permanent storage, add a **free PostgreSQL** database on Render — I can help
   you switch to it later if needed.

---

## Option B — Even simpler: Railway.app

If GitHub feels like too many steps, try **Railway**:
1. Go to https://railway.app → Login with GitHub
2. **"New Project"** → **"Deploy from GitHub repo"** (same repo as above)
3. Railway auto-detects Flask, deploys, gives you a URL. Done.

Railway free trial gives $5/month credit — enough for a family menu.

---

## Need help?
If any step fails, paste the error message to me and I'll walk you through it.
