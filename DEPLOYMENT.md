# 🚀 Deployment Guide

This guide will help you deploy the Traffic Congestion Predictor to **Render** (Backend) and **Vercel** (Frontend).

---

## 📋 Prerequisites

- GitHub repository linked to your account (already done ✅)
- Render account: [render.com](https://render.com)
- Vercel account: [vercel.com](https://vercel.com)

---

## 1️⃣ Deploy Backend to Render

### Step 1: Create a new service on Render
1. Go to [render.com/dashboard](https://render.com/dashboard)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository:
   - Authorize GitHub if prompted
   - Select repository: `traffic_congenstion`
   - Branch: `main`

### Step 2: Configure the service
- **Name:** `traffic-congestion-backend`
- **Environment:** Python 3
- **Region:** Choose closest to you
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Free (or Starter for better performance)

### Step 3: Environment Variables (Optional)
If using PostgreSQL, add:
```
DATABASE_URL=postgresql://user:password@host:port/dbname
```
Leave empty to use SQLite (default).

### Step 4: Deploy
Click **"Create Web Service"**
- Render will automatically build and deploy
- Your backend will be live at: `https://traffic-congestion-backend.onrender.com`

---

## 2️⃣ Deploy Frontend to Vercel

### Step 1: Create a new project on Vercel
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import GitHub repository:
   - Select: `traffic_congenstion`
   - Branch: `main`

### Step 2: Configure the project
- **Framework Preset:** React
- **Root Directory:** `frontend`
- **Build Command:** `npm install && npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

### Step 3: Environment Variables
Add the backend URL:
```
VITE_BACKEND_URL=https://traffic-congestion-backend.onrender.com/api
```

### Step 4: Deploy
Click **"Deploy"**
- Vercel will automatically build and deploy
- Your frontend will be live at: `https://traffic-congestion.vercel.app`

---

## 3️⃣ Update Frontend API Connection

After deployment, update the API endpoint in your frontend:

**File:** `frontend/src/App.jsx`

Replace:
```javascript
const BACKEND_URL = "http://localhost:8001/api";
```

With:
```javascript
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8001/api";
```

### Step 4: Deploy Updated Frontend
Push changes to GitHub:
```bash
git add .
git commit -m "Update API endpoint for production"
git push origin main
```

Vercel will automatically redeploy!

---

## ✅ Verification Checklist

After deployment:
- [ ] Backend API is accessible: `https://your-backend.onrender.com/docs`
- [ ] Frontend loads: `https://your-frontend.vercel.app`
- [ ] Route Advisor works (click "Find Best Routes")
- [ ] Predictions display correctly
- [ ] Map renders without errors
- [ ] Database is seeded with traffic data

---

## 🔧 Troubleshooting

### Backend not loading
- Check Render logs: Dashboard → Your Service → Logs
- Ensure `requirements.txt` has all dependencies
- Verify Python version is 3.12+

### Frontend shows blank page
- Check browser console: F12 → Console tab
- Verify `VITE_BACKEND_URL` is set correctly
- Check Vercel build logs for errors

### API calls fail
- Ensure backend URL is correct in frontend
- Check CORS middleware in `backend/main.py`
- Backend should allow all origins: `allow_origins=["*"]`

---

## 📊 Performance Tips

1. **For Render Free Tier:**
   - Backend may spin down after inactivity
   - First request after idle takes ~30 seconds
   - Upgrade to Starter tier for always-on deployment

2. **For Vercel Free Tier:**
   - Great for static frontend
   - Supports unlimited deployments
   - Auto-scaling on high traffic

3. **Optimize Database:**
   - Use PostgreSQL for production (faster than SQLite)
   - Add indexes on frequently queried columns

---

## 🎯 Production Recommendations

1. **Security:**
   - Set `DATABASE_URL` as private environment variable
   - Use HTTPS only (both platforms provide this)
   - Add authentication/rate limiting

2. **Monitoring:**
   - Enable error tracking (Sentry, LogRocket)
   - Set up uptime monitoring
   - Monitor API response times

3. **Scaling:**
   - Upgrade Render to Standard tier for better performance
   - Use CDN for static assets
   - Implement caching strategies

---

## 🔗 Useful Links

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/concepts/)
- [React Vite Deployment](https://vitejs.dev/guide/static-deploy.html)

---

**Last Updated:** July 15, 2026
**Status:** ✅ Ready for Production
