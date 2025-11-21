from pydantic import BaseModel, confloat
from typing import Optional, List, Dict, Any


class AllocateGrandTotalIn(BaseModel):
    # One grand total for the entire year (all months, all branches)
    grand_total_estimated_sales: confloat(gt=0)
    brand_ids: Optional[List[int]] = None
    # NEW: return grouped (brand->branch->months)
    include_grouped_data: bool = True


class AllocateGrandTotalOut(BaseModel):
    grand_total_estimated_sales: float
    rows_considered: int
    rows_written: int
    baseline_sum: float
    applied_factor: float
    skipped_zero_baseline: int
    data: Optional[List[dict]] = None
