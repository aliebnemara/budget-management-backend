# 🚀 BACKEND DEPLOYMENT GUIDE

## 🎯 **Deploy FastAPI Backend to Render.com**

### **Step 1: Create GitHub Repository for Backend**

1. Go to: https://github.com/new
2. Repository name: `budget-management-backend`
3. Description: `FastAPI backend for budget management system`
4. Keep it **Private** (or Public if you want)
5. **DO NOT** initialize with README
6. Click **"Create repository"**

### **Step 2: Push Backend Code to GitHub**

Run these commands:
```bash
cd /home/user/backend/Backend

# Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/budget-management-backend.git

# Push code
git push -u origin main
```

### **Step 3: Deploy to Render.com**

1. **Go to:** https://render.com/
2. **Click:** "Get Started" or "Sign Up"
3. **Sign in with GitHub**
4. **Click:** "New" → "Web Service"
5. **Connect Repository:** Select `budget-management-backend`

### **Step 4: Configure Render**

```
Service Name: budget-management-api
Region: Oregon (US West) or closest to you
Branch: main
Root Directory: (leave empty)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn src.main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
```

### **Step 5: Add Environment Variables**

In Render dashboard, add these environment variables:

```
DATABASE_URL=sqlite:///./budget.db
SECRET_KEY=your-secret-key-here-change-this
CORS_ORIGINS=https://budget-management-system-xxxx.vercel.app
```

### **Step 6: Deploy!**

- Click **"Create Web Service"**
- Wait 2-3 minutes for deployment
- You'll get a URL like: `https://budget-management-api.onrender.com`

---

## 🔗 **Connect Frontend to Backend**

### **Step 1: Update Vercel Environment Variable**

1. Go to your Vercel project: https://vercel.com/dashboard
2. Click your project: `budget-management-system`
3. Go to: **Settings** → **Environment Variables**
4. Add new variable:
   ```
   Name: VITE_API_BASE_URL
   Value: https://budget-management-api.onrender.com
   ```
5. Click **"Save"**
6. **Redeploy** your frontend (it will auto-deploy)

---

## ✅ **Alternative: Deploy Backend to Other Platforms**

### **Option 2: Railway.app**
- Similar to Render
- Free tier available
- Easier database setup
- Guide: https://railway.app/new

### **Option 3: Fly.io**
- Free tier with more resources
- Better performance
- Requires Docker
- Guide: https://fly.io/docs/

---

## 🧪 **Test Your Deployment**

### **Test Backend:**
```bash
curl https://your-backend-url.onrender.com/api/health
```

### **Test Login from Frontend:**
1. Open your Vercel app
2. Try to login with your credentials
3. Check browser console for any errors

---

## 🔧 **Troubleshooting**

### **CORS Errors:**
Add your Vercel URL to backend CORS settings in `src/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Database Issues:**
Render free tier uses ephemeral filesystem. For production:
- Use Render PostgreSQL addon (free tier available)
- Or use external database like Supabase

### **Environment Variables:**
Make sure all required env vars are set in Render dashboard

---

## 📝 **Quick Reference**

**Backend URL:** `https://your-api.onrender.com`  
**Frontend URL:** `https://your-app.vercel.app`  
**GitHub Backend:** `https://github.com/YOUR_USERNAME/budget-management-backend`  
**GitHub Frontend:** `https://github.com/aliebnemara/budget-management-system`

---

## 🎉 **After Deployment**

Your complete stack will be:
- ✅ Frontend on Vercel (deployed)
- ✅ Backend on Render (deployed)
- ✅ Database on Render or external
- ✅ Full authentication working
- ✅ All API calls working

---

Need help? Just ask! 😊
