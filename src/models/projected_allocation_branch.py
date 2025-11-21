from pydantic import BaseModel, confloat, field_validator
from typing import Dict, List, Optional

class BranchTotalsIn(BaseModel):
    # Example: {"189": 1_200_000, "190": 900_000}
    # If a branch is omitted or its value is null/missing/<=0, factor=1 is applied (recompute from baseline).
    branch_totals: Dict[str, Optional[confloat(gt=0)]] = {}

    @field_validator("branch_totals")
    @classmethod
    def _keys_to_ints(cls, v: Dict[str, Optional[float]]) -> Dict[int, Optional[float]]:
        out: Dict[int, Optional[float]] = {}
        for k, val in v.items():
            out[int(k)] = float(val) if val not in (None,) else None
        return out  # type: ignore[return-value]

class BranchAllocationResult(BaseModel):
    branch_id: int
    rows_considered: int
    rows_written: int
    baseline_sum: float
    applied_factor: float
    skipped_zero_baseline: int

class BranchTotalsOut(BaseModel):
    results: List[BranchAllocationResult]
    overall_rows_considered: int
    overall_rows_written: int
    overall_baseline_sum: float
    branches_requested: int
    branches_with_allocation: int
    data: Optional[List[dict]] = None