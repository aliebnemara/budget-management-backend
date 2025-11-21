# Budget Management Backend

FastAPI backend for budget management system with authentication and data management.

## 🚀 Quick Deploy

### Deploy to Render (One Click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/aliebnemara/budget-management-backend)

**OR**

Click this link: https://render.com/deploy?repo=https://github.com/aliebnemara/budget-management-backend

---

## ✅ After Deployment:

1. Wait for deployment to complete (2-3 minutes)
2. Copy your backend URL (example: `https://budget-management-api.onrender.com`)
3. Add it to Vercel environment variables:
   - Go to: https://vercel.com/dashboard
   - Select your project
   - Settings → Environment Variables
   - Add: `VITE_API_BASE_URL` = `your-render-url`
4. Redeploy frontend

Your app will be fully functional! 🎉

---

## 📋 Manual Deployment Instructions

If the one-click deploy doesn't work, follow these steps:

### Step 1: Create Web Service on Render
1. Go to: https://dashboard.render.com/
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Select repository: `budget-management-backend`

### Step 2: Configure
```
Name: budget-management-api
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn src.main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
```

### Step 3: Environment Variables
```
DATABASE_URL = sqlite:///./budget.db
SECRET_KEY = your-secret-key-change-this
CORS_ORIGINS = *
```

### Step 4: Deploy
Click "Create Web Service" and wait for deployment.

---

## 🔗 Connect to Frontend

After backend is deployed, update Vercel:

1. Go to Vercel dashboard
2. Select your project: `budget-management-system`
3. Settings → Environment Variables
4. Add new variable:
   - Key: `VITE_API_BASE_URL`
   - Value: Your Render backend URL
5. Redeploy

---

## ✅ Verification

Test your backend:
```bash
curl https://your-backend-url.onrender.com/docs
```

You should see the FastAPI documentation page.

---

## 📞 Support

If you need help, check the deployment logs in Render dashboard or contact support.
