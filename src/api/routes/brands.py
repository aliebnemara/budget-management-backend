from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from src.core.db import get_session, close_session
from src.db.dbtables import Brand, Branch
from src.api.routes.auth import get_current_user

brandsRouter = APIRouter(prefix="/api/brands", tags=["brands"])

# Pydantic models
class BrandCreate(BaseModel):
    brand_id: int
    brand_name: str

class BrandUpdate(BaseModel):
    brand_name: str

class BranchCreate(BaseModel):
    branch_id: int
    branch_name: str
    brand_id: int

class BranchUpdate(BaseModel):
    branch_name: str

class SoftDeleteRequest(BaseModel):
    is_deleted: bool

# Brand endpoints
@brandsRouter.post("/", status_code=status.HTTP_201_CREATED)
def create_brand(brand_data: BrandCreate, current_user: dict = Depends(get_current_user)):
    """Create a new brand"""
    dbs = get_session()
    try:
        # Check if brand_id already exists
        existing = dbs.query(Brand).filter(Brand.id == brand_data.brand_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand with ID {brand_data.brand_id} already exists"
            )
        
        # Create new brand with audit tracking
        new_brand = Brand(
            id=brand_data.brand_id,
            name=brand_data.brand_name,
            is_deleted=False,
            added_by=current_user.get("id")  # Track who created the brand
        )
        dbs.add(new_brand)
        dbs.commit()
        dbs.refresh(new_brand)
        
        return {
            "brand_id": new_brand.id,
            "brand_name": new_brand.name,
            "is_deleted": new_brand.is_deleted,
            "message": "Brand created successfully"
        }
    except IntegrityError:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand ID already exists or database constraint violation"
        )
    except Exception as e:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create brand: {str(e)}"
        )
    finally:
        close_session(dbs)

@brandsRouter.put("/{brand_id}", status_code=status.HTTP_200_OK)
def update_brand(brand_id: int, brand_data: BrandUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing brand"""
    dbs = get_session()
    try:
        brand = dbs.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand with ID {brand_id} not found"
            )
        
        brand.name = brand_data.brand_name
        brand.edited_by = current_user.get("id")  # Track who edited the brand
        brand.edited_at = datetime.now()  # Update edit timestamp
        dbs.commit()
        dbs.refresh(brand)
        
        return {
            "brand_id": brand.id,
            "brand_name": brand.name,
            "message": "Brand updated successfully"
        }
    except Exception as e:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update brand: {str(e)}"
        )
    finally:
        close_session(dbs)

@brandsRouter.patch("/{brand_id}/soft-delete", status_code=status.HTTP_200_OK)
def soft_delete_brand(brand_id: int, delete_request: SoftDeleteRequest, current_user: dict = Depends(get_current_user)):
    """Soft delete/restore a brand by setting is_deleted flag"""
    dbs = get_session()
    try:
        brand = dbs.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand with ID {brand_id} not found"
            )
        
        brand.is_deleted = delete_request.is_deleted
        
        # Track soft delete/restore audit information
        if delete_request.is_deleted:
            brand.deleted_at = datetime.now()
            brand.deleted_by = current_user.get("id")
        else:
            # Restore: clear soft delete tracking
            brand.deleted_at = None
            brand.deleted_by = None
            brand.edited_by = current_user.get("id")  # Track who restored
            brand.edited_at = datetime.now()
        
        dbs.commit()
        dbs.refresh(brand)
        
        action = "deleted" if delete_request.is_deleted else "restored"
        return {
            "brand_id": brand.id,
            "brand_name": brand.name,
            "is_deleted": brand.is_deleted,
            "message": f"Brand {action} successfully"
        }
    except Exception as e:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update brand: {str(e)}"
        )
    finally:
        close_session(dbs)

# Branch endpoints
@brandsRouter.post("/branches", status_code=status.HTTP_201_CREATED)
def create_branch(branch_data: BranchCreate, current_user: dict = Depends(get_current_user)):
    """Create a new branch"""
    dbs = get_session()
    try:
        # Check if brand exists
        brand = dbs.query(Brand).filter(Brand.id == branch_data.brand_id).first()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand with ID {branch_data.brand_id} not found"
            )
        
        # Check if branch_id already exists
        existing = dbs.query(Branch).filter(Branch.id == branch_data.branch_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Branch with ID {branch_data.branch_id} already exists"
            )
        
        # Create new branch with audit tracking
        new_branch = Branch(
            id=branch_data.branch_id,
            name=branch_data.branch_name,
            brand_id=branch_data.brand_id,
            is_deleted=False,
            added_by=current_user.get("id")  # Track who created the branch
        )
        dbs.add(new_branch)
        dbs.commit()
        dbs.refresh(new_branch)
        
        return {
            "branch_id": new_branch.id,
            "branch_name": new_branch.name,
            "brand_id": new_branch.brand_id,
            "is_deleted": new_branch.is_deleted,
            "message": "Branch created successfully"
        }
    except IntegrityError:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch ID already exists or database constraint violation"
        )
    except Exception as e:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}"
        )
    finally:
        close_session(dbs)

@brandsRouter.put("/branches/{branch_id}", status_code=status.HTTP_200_OK)
def update_branch(branch_id: int, branch_data: BranchUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing branch"""
    dbs = get_session()
    try:
        branch = dbs.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branch with ID {branch_id} not found"
            )
        
        branch.name = branch_data.branch_name
        branch.edited_by = current_user.get("id")  # Track who edited the branch
        branch.edited_at = datetime.now()  # Update edit timestamp
        dbs.commit()
        dbs.refresh(branch)
        
        return {
            "branch_id": branch.id,
            "branch_name": branch.name,
            "brand_id": branch.brand_id,
            "message": "Branch updated successfully"
        }
    except Exception as e:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update branch: {str(e)}"
        )
    finally:
        close_session(dbs)

@brandsRouter.patch("/branches/{branch_id}/soft-delete", status_code=status.HTTP_200_OK)
def soft_delete_branch(branch_id: int, delete_request: SoftDeleteRequest, current_user: dict = Depends(get_current_user)):
    """Soft delete/restore a branch by setting is_deleted flag"""
    dbs = get_session()
    try:
        branch = dbs.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branch with ID {branch_id} not found"
            )
        
        branch.is_deleted = delete_request.is_deleted
        
        # Track soft delete/restore audit information
        if delete_request.is_deleted:
            branch.deleted_at = datetime.now()
            branch.deleted_by = current_user.get("id")
        else:
            # Restore: clear soft delete tracking
            branch.deleted_at = None
            branch.deleted_by = None
            branch.edited_by = current_user.get("id")  # Track who restored
            branch.edited_at = datetime.now()
        
        dbs.commit()
        dbs.refresh(branch)
        
        action = "deleted" if delete_request.is_deleted else "restored"
        return {
            "branch_id": branch.id,
            "branch_name": branch.name,
            "brand_id": branch.brand_id,
            "is_deleted": branch.is_deleted,
            "message": f"Branch {action} successfully"
        }
    except Exception as e:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update branch: {str(e)}"
        )
    finally:
        close_session(dbs)

@brandsRouter.delete("/branches/{branch_id}/permanent", status_code=status.HTTP_200_OK)
def permanent_delete_branch(branch_id: int, current_user: dict = Depends(get_current_user)):
    """Permanently delete a branch from the database"""
    dbs = get_session()
    try:
        branch = dbs.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branch with ID {branch_id} not found"
            )
        
        branch_name = branch.name
        brand_id = branch.brand_id
        
        # Permanently delete from database
        dbs.delete(branch)
        dbs.commit()
        
        return {
            "branch_id": branch_id,
            "branch_name": branch_name,
            "brand_id": brand_id,
            "message": f"Branch '{branch_name}' (ID: {branch_id}) permanently deleted from database"
        }
    except Exception as e:
        dbs.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to permanently delete branch: {str(e)}"
        )
    finally:
        close_session(dbs)
