# services/branch_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import joinedload
from src.core.db import get_session, close_session
from src.db.dbtables import Brand, Branch

def list_branches(brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Returns a simple list of branches: [{branch_id, branch_name, brand_id, brand_name}, ...]
    If brand_id is provided, filters to that brand only.
    Filters out soft-deleted brands and branches.
    """
    dbs = get_session()
    try:
        # Load brands with branches for one pass, then flatten
        # Filter out soft-deleted brands
        q = dbs.query(Brand).options(joinedload(Brand.branches)).filter(Brand.is_deleted == False)
        if brand_id is not None:
            q = q.filter(Brand.id == brand_id)
        
        # Order brands by ID for consistency
        q = q.order_by(Brand.id)

        rows: List[Dict[str, Any]] = []
        for brand in q.all():
            # Filter out soft-deleted branches
            active_branches = [br for br in brand.branches if not br.is_deleted]
            for br in sorted(active_branches, key=lambda x: (x.name or "", x.id)):
                rows.append({
                    "branch_id": br.id,
                    "branch_name": br.name,
                    "brand_id": brand.id,
                    "brand_name": brand.name,
                })

        # Sort final output by brand ID then branch ID for consistency
        rows.sort(key=lambda r: (r["brand_id"], r["branch_id"]))
        return rows
    finally:
        close_session(dbs)
