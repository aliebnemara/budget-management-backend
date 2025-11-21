from pydantic import BaseModel, Field, ConfigDict
from typing import List,Optional


class BrandModel(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class BranchModel(BaseModel):
    id: int
    brand_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

# --- month row coming from your DataFrame ---
class MonthData(BaseModel):
    month: int
    trade_on_off: Optional[float] = None
    ramadan_eid_pct: Optional[float] = None
    muharram_pct: Optional[float] = None
    eid2_pct: Optional[float] = None

# --- nested outputs for your endpoint ---
class BranchOut(BranchModel):
    months: List[MonthData] = []

class BrandOut(BrandModel):
    branches: List[BranchOut] = []