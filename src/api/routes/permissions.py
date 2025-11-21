"""
API endpoints for role permissions management
Only accessible by Super Admin
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.core.db import get_session, close_session
from src.db.dbtables import Role
from src.api.routes.auth import get_current_user

permissionsRouter = APIRouter()

# Pydantic models
class PermissionUpdate(BaseModel):
    permissions: Dict

class RolePermissionsResponse(BaseModel):
    id: int
    name: str
    description: str
    permissions: Dict

def is_super_admin(current_user: dict) -> bool:
    """Check if current user is a super admin"""
    return any(role.get('name') == 'super_admin' for role in current_user.get('roles', []))

@permissionsRouter.get("/roles/permissions", response_model=List[RolePermissionsResponse])
async def get_all_role_permissions(current_user: dict = Depends(get_current_user)):
    """
    Get permissions for all roles
    Only accessible by Super Admin
    """
    # Check if user is super admin
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Super Admin can view role permissions"
        )
    
    session = get_session()
    try:
        roles = session.query(Role).all()
        
        result = []
        for role in roles:
            result.append({
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions or {}
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching role permissions: {str(e)}")
    finally:
        close_session(session)

@permissionsRouter.get("/roles/{role_id}/permissions", response_model=RolePermissionsResponse)
async def get_role_permissions(role_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get permissions for a specific role
    Only accessible by Super Admin
    """
    # Check if user is super admin
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Super Admin can view role permissions"
        )
    
    session = get_session()
    try:
        role = session.query(Role).filter(Role.id == role_id).first()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching role permissions: {str(e)}")
    finally:
        close_session(session)

@permissionsRouter.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: int,
    permission_data: PermissionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update permissions for a specific role
    Only accessible by Super Admin
    """
    # Check if user is super admin
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Super Admin can update role permissions"
        )
    
    session = get_session()
    try:
        role = session.query(Role).filter(Role.id == role_id).first()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Prevent modifying super_admin permissions
        if role.name == 'super_admin':
            raise HTTPException(
                status_code=403,
                detail="Cannot modify Super Admin permissions"
            )
        
        # Update permissions
        role.permissions = permission_data.permissions
        session.commit()
        
        return {
            "message": "Role permissions updated successfully",
            "role": {
                "id": role.id,
                "name": role.name,
                "permissions": role.permissions
            }
        }
        
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating role permissions: {str(e)}")
    finally:
        close_session(session)

@permissionsRouter.get("/permissions/structure")
async def get_permissions_structure(current_user: dict = Depends(get_current_user)):
    """
    Get the structure of available permissions
    Returns the permission categories and actions
    """
    # Check if user is super admin
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Super Admin can view permissions structure"
        )
    
    return {
        "categories": [
            {
                "key": "users",
                "label": "User Management",
                "actions": ["view", "create", "edit", "delete"],
                "description": "Manage user accounts and access"
            },
            {
                "key": "brands",
                "label": "Brand Management",
                "actions": ["view", "create", "edit", "delete"],
                "description": "Manage brand data and settings"
            },
            {
                "key": "branches",
                "label": "Branch Management",
                "actions": ["view", "create", "edit", "delete"],
                "description": "Manage branch data and operations"
            },
            {
                "key": "financial_data",
                "label": "Financial Data",
                "actions": ["view", "create", "edit", "delete"],
                "description": "Access and modify financial information"
            },
            {
                "key": "reports",
                "label": "Reports",
                "actions": ["view", "create", "edit", "delete"],
                "description": "Generate and manage reports"
            },
            {
                "key": "system_settings",
                "label": "System Settings",
                "actions": ["view", "create", "edit", "delete"],
                "description": "Configure system-wide settings"
            },
            {
                "key": "role_permissions",
                "label": "Role Permissions",
                "actions": ["view", "edit"],
                "description": "Manage role-based permissions (Super Admin only)"
            }
        ]
    }
