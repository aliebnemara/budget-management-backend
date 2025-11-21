from fastapi import FastAPI
from src.api.routes import budget, auth, permissions, brands, daily_sales
from dotenv import load_dotenv
from src.core.db import init_db
from fastapi.middleware.cors import CORSMiddleware

load_dotenv() 
app = FastAPI()

# Initialize the database connection
if init_db() is not None:
    print("Failed to connect to the database")
    exit(1)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # or ["*"] for dev-only (no credentials)
    allow_methods=["*"],          # or list specific methods
    allow_headers=["*"],          # or list specific headers
)

# Register routers
app.include_router(auth.authRouter)
app.include_router(auth.usersRouter)
app.include_router(budget.budgetRouter)
app.include_router(permissions.permissionsRouter, prefix="/api/permissions", tags=["permissions"])
app.include_router(brands.brandsRouter)
app.include_router(daily_sales.dailySalesRouter)

print("✅ FastAPI app initialized with authentication, permissions, brands, and daily sales routes")
print("   Login at: http://localhost:8000/api/auth/login")
