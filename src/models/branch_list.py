from pydantic import BaseModel
from typing import List

class BranchLite(BaseModel):
    branch_id: int
    branch_name: str
    brand_id: int
    brand_name: str

class BranchListOut(BaseModel):
    branches: List[BranchLite]