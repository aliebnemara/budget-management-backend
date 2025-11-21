from pydantic import BaseModel, confloat, field_validator, conint
from typing import Dict, List, Optional

class BranchMonthlyTotalsIn(BaseModel):
    # Example:
    # {
    #   "189": {"1": 100000, "2": 120000, "3": null},
    #   "190": {"1": 90000}
    # }
    # Missing or null => factor=1 (recompute) for those (branch, month).
    branch_month_totals: Dict[str, Dict[str, Optional[confloat(gt=0)]]] = {}

    @field_validator("branch_month_totals")
    @classmethod
    def _normalize(cls, v: Dict[str, Dict[str, Optional[float]]]) -> Dict[int, Dict[int, Optional[float]]]:
        out: Dict[int, Dict[int, Optional[float]]] = {}
        for b, months in v.items():
            bid = int(b)
            out[bid] = {}
            for m, val in months.items():
                mi = int(m)
                if mi < 1 or mi > 12:
                    raise ValueError(f"Invalid month: {m}")
                out[bid][mi] = float(val) if val not in (None,) else None
        return out  # type: ignore[return-value]

class BranchMonthlyAllocationResult(BaseModel):
    branch_id: int
    month: conint(ge=1, le=12)
    rows_considered: int
    rows_written: int
    baseline_sum: float
    applied_factor: float
    skipped_zero_baseline: int

class BranchMonthlyTotalsOut(BaseModel):
    results: List[BranchMonthlyAllocationResult]
    overall_rows_considered: int
    overall_rows_written: int
    overall_baseline_sum: float
    pairs_requested: int
    pairs_with_allocation: int
    data: Optional[List[dict]] = None
