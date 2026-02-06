# Deployment Guide

This guide covers deploying both the backend and frontend to production.

## 🚀 Quick Start (Recommended Path)

**Fastest way to deploy**: Railway (Backend) + Vercel (Frontend)

### Step 1: Deploy Backend to Railway

1. Go to [railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect it's Python. If not:
   - Set root directory to `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable:
   - Go to Variables tab
   - Add `GEMINI_API_KEY` = your Gemini API key
   - Add `FRONTEND_URLS` = your frontend URL (you'll update this after deploying frontend)
6. Copy your Railway backend URL (e.g., `https://your-app.railway.app`)

### Step 2: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click "Add New Project" → Import your GitHub repo
3. Configure:
   - Root directory: `frontend`
   - Framework preset: Vite (auto-detected)
   - Build command: `npm run build` (auto-detected)
   - Output directory: `dist` (auto-detected)
4. Add environment variable:
   - Go to Project Settings → Environment Variables
   - Add `VITE_API_URL` = your Railway backend URL from Step 1
5. Deploy!

### Step 3: Update Backend CORS

1. Go back to Railway dashboard
2. Update `FRONTEND_URLS` variable to include your Vercel URL:
   ```
   https://your-frontend.vercel.app,http://localhost:5173
   ```
3. Railway will auto-redeploy

**Done!** Your app is live. Test it by visiting your Vercel URL.

---

## Quick Deploy Options

### Option 1: Railway (Backend) + Vercel (Frontend) - Recommended
- **Backend**: Railway (free tier available)
- **Frontend**: Vercel (free tier, excellent for React)

### Option 2: Render (Both)
- **Backend**: Render Web Service
- **Frontend**: Render Static Site

### Option 3: Fly.io (Backend) + Netlify (Frontend)
- **Backend**: Fly.io
- **Frontend**: Netlify

---

## Backend Deployment

### Railway (Easiest)

1. **Install Railway CLI** (optional, can use web UI):
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Deploy**:
   ```bash
   cd backend
   railway init
   railway up
   ```

3. **Set Environment Variables**:
   - In Railway dashboard, go to your project → Variables
   - Add: `GEMINI_API_KEY=your_key_here`

4. **Configure Port**:
   Railway automatically sets `PORT` env var. Update `main.py` to use it:
   ```python
   # Already handled in the Dockerfile/startup
   ```

**Note**: Railway auto-detects Python projects and installs from `requirements.txt`.

### Render

1. **Create Account**: Go to [render.com](https://render.com)

2. **New Web Service**:
   - Connect your GitHub repo
   - Select the `backend` directory
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3

3. **Environment Variables**:
   - Add `GEMINI_API_KEY` in the Environment tab

4. **Deploy**: Render will auto-deploy on git push

### Fly.io

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Initialize** (in backend directory):
   ```bash
   cd backend
   fly launch
   ```

3. **Set Secrets**:
   ```bash
   fly secrets set GEMINI_API_KEY=your_key_here
   ```

4. **Deploy**:
   ```bash
   fly deploy
   ```

---

## Frontend Deployment

### Update API URL for Production

Before deploying, update the frontend to use environment variables for the API URL.

The frontend code already uses `http://localhost:8000` - we'll make this configurable.

### Vercel (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   cd frontend
   vercel
   ```

3. **Set Environment Variables**:
   - In Vercel dashboard → Project Settings → Environment Variables
   - Add: `VITE_API_URL=https://your-backend-url.railway.app` (or your backend URL)

4. **Update Frontend Code**:
   The frontend needs to read from env var. See `frontend/src/config.js` (we'll create this).

5. **Redeploy**: Vercel auto-deploys on git push, or run `vercel --prod`

### Netlify

1. **Install Netlify CLI**:
   ```bash
   npm i -g netlify-cli
   ```

2. **Deploy**:
   ```bash
   cd frontend
   netlify deploy --prod
   ```

3. **Set Environment Variables**:
   - In Netlify dashboard → Site Settings → Environment Variables
   - Add: `VITE_API_URL=https://your-backend-url`

4. **Build Settings** (if using Netlify UI):
   - Build command: `npm run build`
   - Publish directory: `dist`

### Render (Static Site)

1. **New Static Site**:
   - Connect GitHub repo
   - Root directory: `frontend`
   - Build command: `npm install && npm run build`
   - Publish directory: `frontend/dist`

2. **Environment Variables**:
   - Add `VITE_API_URL` in Environment tab

---

## Docker Deployment (Alternative)

### Backend Dockerfile

A `Dockerfile` is included in the backend directory. Use it for:
- Docker-based platforms (Railway, Fly.io, AWS ECS, etc.)
- Self-hosting on a VPS

**Build and run locally**:
```bash
cd backend
docker build -t sovereign-scan-backend .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key sovereign-scan-backend
```

---

## Post-Deployment Checklist

1. ✅ Backend is accessible (test: `curl https://your-backend-url/`)
2. ✅ Environment variables are set (especially `GEMINI_API_KEY`)
3. ✅ Frontend `VITE_API_URL` points to your backend URL
4. ✅ CORS is configured to allow your frontend domain
5. ✅ Test the full flow: Enter URL → Get results

---

## Updating CORS for Production

The backend currently allows `localhost:5173`. After deploying, update `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-frontend-domain.vercel.app",  # Add your production URL
    ],
    # ... rest of config
)
```

Or use environment variable:
```python
import os
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
allow_origins=[FRONTEND_URL]
```

---

## Troubleshooting

### Backend Issues

- **Port binding**: Ensure backend listens on `0.0.0.0`, not `127.0.0.1`
- **Timeout**: Some platforms have request timeouts. Consider adding async processing for long-running analyses
- **Memory**: Gemini API calls can be memory-intensive. Ensure your plan has enough RAM

### Frontend Issues

- **CORS errors**: Update backend CORS settings to include your frontend domain
- **API not found**: Verify `VITE_API_URL` is set correctly and rebuild
- **Build fails**: Check Node version (Vite requires Node 18+)

### Environment Variables

- **Vite**: Must prefix with `VITE_` to be accessible in browser
- **Backend**: Use platform-specific secret management (Railway Variables, Render Env, etc.)
