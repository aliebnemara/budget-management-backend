# Budget Management System - Backend API

FastAPI backend for the budget management system with authentication, role-based access control, and comprehensive data management.

## 🚀 ONE-CLICK DEPLOY (Choose One)

### Option 1: Railway (Recommended - Easiest)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/HB_Q_D?referralCode=alphasec)

**Click the button above, then:**
1. Sign in with GitHub
2. Click "Deploy Now"
3. Wait 2 minutes
4. Copy your Railway URL
5. Done! ✅

### Option 2: Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**Click the button above, then:**
1. Sign in with GitHub
2. Select this repository
3. Click "Apply"
4. Wait 3 minutes
5. Done! ✅

### Option 3: Fly.io
```bash
flyctl launch
flyctl deploy
```

## 📋 Environment Variables

After deployment, add these environment variables:

```env
DATABASE_URL=sqlite:///./budget.db
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=*
```

## 🔗 Connect to Frontend

After deploying, update your Vercel frontend with:

**Environment Variable:**
```
VITE_API_BASE_URL = https://your-backend-url.railway.app
```

## 📝 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn src.main:app --reload --port 8000
```

## 🧪 API Documentation

Once deployed, visit:
- Swagger UI: `https://your-backend-url/docs`
- ReDoc: `https://your-backend-url/redoc`

## 🏗️ Tech Stack

- **Framework:** FastAPI
- **Database:** SQLite (with SQLAlchemy ORM)
- **Authentication:** JWT tokens
- **CORS:** Enabled for all origins
- **Documentation:** Auto-generated OpenAPI

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user

### Budget Management
- `GET /api/budget/` - Get budget data
- `POST /api/budget/` - Create/update budget
- `DELETE /api/budget/{id}` - Delete budget entry

### Brands & Branches
- `GET /api/brands/` - List all brands
- `GET /api/brands/{id}/branches` - Get brand branches

### Daily Sales
- `GET /api/daily-sales/` - Get sales data
- `POST /api/daily-sales/import` - Import sales data

### User Management (Admin only)
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

## 🔐 Default Users

After initialization, you can login with:

**Super Admin:**
- Username: `admin`
- Password: (set during initialization)

## 📄 License

Private - Budget Management System

## 🆘 Support

For issues or questions, contact the development team.
