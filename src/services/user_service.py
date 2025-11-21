"""
User service for database operations.
Handles all user CRUD operations with the database.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.db.dbtables import User, Role
from src.core.db import get_session, close_session
import hashlib


def hash_password(password: str) -> str:
    """Simple SHA256 password hashing (for demo purposes)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(plain_password) == hashed_password


def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username from database"""
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return None
        
        return user_to_dict(user)
    finally:
        close_session(session)


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID from database"""
    session = get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return None
        
        return user_to_dict(user)
    finally:
        close_session(session)


def get_all_users() -> List[Dict]:
    """Get all users from database"""
    session = get_session()
    try:
        users = session.query(User).all()
        return [user_to_dict(user) for user in users]
    finally:
        close_session(session)


def create_user(user_data: Dict) -> Dict:
    """Create a new user in database"""
    session = get_session()
    try:
        # Create user instance
        new_user = User(
            username=user_data['username'],
            password_hash=hash_password(user_data['password']),
            email=user_data.get('email'),
            full_name=user_data.get('full_name'),
            is_active=user_data.get('is_active', True)
        )
        
        # Add roles
        if 'roles' in user_data:
            for role_name in user_data['roles']:
                role = session.query(Role).filter_by(name=role_name).first()
                if role:
                    new_user.roles.append(role)
        
        # Add brands
        if 'brand_ids' in user_data:
            from src.db.dbtables import Brand
            for brand_id in user_data['brand_ids']:
                brand = session.query(Brand).filter_by(id=brand_id).first()
                if brand:
                    new_user.brands.append(brand)
        
        # Add branches
        if 'branch_ids' in user_data:
            from src.db.dbtables import Branch
            for branch_id in user_data['branch_ids']:
                branch = session.query(Branch).filter_by(id=branch_id).first()
                if branch:
                    new_user.branches.append(branch)
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        return user_to_dict(new_user)
    except Exception as e:
        session.rollback()
        raise e
    finally:
        close_session(session)


def update_user(user_id: int, user_data: Dict) -> Dict:
    """Update user in database"""
    session = get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Update basic fields
        if 'email' in user_data:
            user.email = user_data['email']
        if 'full_name' in user_data:
            user.full_name = user_data['full_name']
        if 'password' in user_data and user_data['password']:
            user.password_hash = hash_password(user_data['password'])
        if 'is_active' in user_data:
            user.is_active = user_data['is_active']
        
        # Update roles
        if 'roles' in user_data:
            user.roles.clear()
            for role_name in user_data['roles']:
                role = session.query(Role).filter_by(name=role_name).first()
                if role:
                    user.roles.append(role)
        
        # Update brands
        if 'brand_ids' in user_data:
            from src.db.dbtables import Brand
            user.brands.clear()
            for brand_id in user_data['brand_ids']:
                brand = session.query(Brand).filter_by(id=brand_id).first()
                if brand:
                    user.brands.append(brand)
        
        # Update branches
        if 'branch_ids' in user_data:
            from src.db.dbtables import Branch
            user.branches.clear()
            for branch_id in user_data['branch_ids']:
                branch = session.query(Branch).filter_by(id=branch_id).first()
                if branch:
                    user.branches.append(branch)
        
        session.commit()
        session.refresh(user)
        
        return user_to_dict(user)
    except Exception as e:
        session.rollback()
        raise e
    finally:
        close_session(session)


def delete_user(user_id: int) -> bool:
    """Delete user from database"""
    session = get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return False
        
        session.delete(user)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        close_session(session)


def user_to_dict(user: User) -> Dict:
    """Convert User model to dictionary"""
    return {
        'id': user.id,
        'username': user.username,
        'password_hash': user.password_hash,  # CRITICAL: Include password hash for authentication
        'email': user.email,
        'full_name': user.full_name,
        'is_active': user.is_active,
        'roles': [{
            'id': role.id, 
            'name': role.name,
            'permissions': role.permissions or {}  # CRITICAL: Include permissions JSONB
        } for role in user.roles],
        'brands': [brand.id for brand in user.brands],
        'branches': [branch.id for branch in user.branches],
        'brand_access': [brand.id for brand in user.brands],
        'branch_access': [branch.id for branch in user.branches],
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None
    }
