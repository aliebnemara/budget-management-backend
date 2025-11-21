from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import jwt

# Import database user service
from src.services.user_service import (
    get_user_by_username, 
    get_user_by_id,
    get_all_users,
    create_user as db_create_user,
    update_user as db_update_user,
    delete_user as db_delete_user,
    verify_password
)

authRouter = APIRouter(prefix="/api/auth", tags=["Authentication"])

# JWT Configuration
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user

@authRouter.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - accepts username and password, returns access and refresh tokens"""
    # Find user by username in database
    user = get_user_by_username(form_data.username)
    
    if not user or not verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    
    # Return user data with tokens (exclude password_hash)
    user_data = {k: v for k, v in user.items() if k != "password_hash"}
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_data
    }

@authRouter.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    # Return user data (exclude password_hash)
    return {k: v for k, v in current_user.items() if k != "password_hash"}

@authRouter.post("/refresh")
async def refresh_token(refresh_token_data: dict):
    """Refresh access token using refresh token"""
    refresh_token = refresh_token_data.get("refresh_token")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    # Create new access token
    access_token = create_access_token(data={"sub": username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

print("✅ Authentication routes initialized (database-backed)")
print("   Default admin credentials:")
print("   Username: admin")
print("   Password: Admin@123")

@authRouter.get("/users")
async def get_all_users_endpoint(current_user: dict = Depends(get_current_user)):
    """Get all users (requires users.view permission)"""
    # Check if user has users.view permission
    is_super_admin = any(role.get("name") == "super_admin" for role in current_user.get("roles", []))
    
    # Check if user has users.view permission from any role
    has_view_permission = any(
        role.get("permissions", {}).get("users", {}).get("view", False)
        for role in current_user.get("roles", [])
    )
    
    if not is_super_admin and not has_view_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users"
        )
    
    # Return all users from database (exclude password_hash)
    users_list = get_all_users()
    return [{k: v for k, v in user.items() if k != "password_hash"} for user in users_list]

@authRouter.get("/system-data")
async def get_system_data(current_user: dict = Depends(get_current_user)):
    """Get system data for dropdowns (brands, branches, roles) - filtered by user permissions"""
    # Simulating loading delay for better UX
    import asyncio
    await asyncio.sleep(0.3)  # 300ms delay for smooth loading experience
    
    from src.services.branch_service import list_branches
    
    # Get real branches from database
    all_branches = list_branches()
    
    # Check if user is super_admin (has access to all brands/branches)
    is_super_admin = any(role.get("name") == "super_admin" for role in current_user.get("roles", []))
    
    # Filter branches based on user permissions
    if is_super_admin:
        # Super admin sees all branches
        branches_data = all_branches
    else:
        # Regular users only see their assigned branches
        user_branch_ids = current_user.get("branch_access", [])
        if user_branch_ids:
            # User has specific branch assignments
            branches_data = [b for b in all_branches if b["branch_id"] in user_branch_ids]
        else:
            # User has no branch restrictions (sees all)
            branches_data = all_branches
    
    # Extract unique brands from filtered branches
    brands_dict = {}
    for branch in branches_data:
        brand_id = branch["brand_id"]
        if brand_id not in brands_dict:
            brands_dict[brand_id] = {
                "id": brand_id,
                "name": branch["brand_name"]
            }
    
    # Filter brands further based on user brand access
    if not is_super_admin:
        user_brand_ids = current_user.get("brand_access", [])
        if user_brand_ids:
            # Filter to only user's assigned brands
            brands_dict = {bid: brand for bid, brand in brands_dict.items() if bid in user_brand_ids}
    
    # Convert to sorted list
    brands_list = sorted(brands_dict.values(), key=lambda x: x["name"])
    
    # Format branches for frontend
    branches_list = [
        {
            "id": branch["branch_id"],
            "name": branch["branch_name"],
            "brand_id": branch["brand_id"]
        }
        for branch in branches_data
    ]
    
    return {
        "roles": [
            {"id": 1, "name": "super_admin", "description": "Full system access"},
            {"id": 2, "name": "admin", "description": "Brand-level administrator"},
            {"id": 3, "name": "manager", "description": "Branch manager"},
            {"id": 4, "name": "viewer", "description": "Read-only access"}
        ],
        "brands": brands_list,
        "branches": branches_list
    }

# Create a router for user management endpoints under /api/users
from fastapi import APIRouter as FastAPIRouter
usersRouter = FastAPIRouter(prefix="/api/users", tags=["User Management"])

@usersRouter.post("")
async def create_user(user_data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new user (requires users.create permission)"""
    # Check if user has users.create permission
    is_super_admin = any(role.get("name") == "super_admin" for role in current_user.get("roles", []))
    has_create_permission = any(
        role.get("permissions", {}).get("users", {}).get("create", False)
        for role in current_user.get("roles", [])
    )
    
    if not is_super_admin and not has_create_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create users"
        )
    
    # Validate required fields
    required_fields = ["username", "email", "password", "roles"]
    for field in required_fields:
        if field not in user_data or not user_data[field]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Check if username already exists
    existing_user = get_user_by_username(user_data["username"])
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user in database
    try:
        new_user = db_create_user(user_data)
        # Return user without password_hash
        return {k: v for k, v in new_user.items() if k != "password_hash"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@usersRouter.put("/{user_id}")
async def update_user(user_id: int, user_data: dict, current_user: dict = Depends(get_current_user)):
    """Update an existing user (requires users.edit permission)"""
    # Check if user has users.edit permission
    is_super_admin = any(role.get("name") == "super_admin" for role in current_user.get("roles", []))
    has_edit_permission = any(
        role.get("permissions", {}).get("users", {}).get("edit", False)
        for role in current_user.get("roles", [])
    )
    
    if not is_super_admin and not has_edit_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit users"
        )
    
    # Update user in database
    try:
        updated_user = db_update_user(user_id, user_data)
        # Return updated user without password_hash
        return {k: v for k, v in updated_user.items() if k != "password_hash"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@usersRouter.delete("/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a user (requires users.delete permission)"""
    # Check if user has users.delete permission
    is_super_admin = any(role.get("name") == "super_admin" for role in current_user.get("roles", []))
    has_delete_permission = any(
        role.get("permissions", {}).get("users", {}).get("delete", False)
        for role in current_user.get("roles", [])
    )
    
    if not is_super_admin and not has_delete_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete users"
        )
    
    # Prevent deleting yourself
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete user from database
    try:
        success = db_delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )
