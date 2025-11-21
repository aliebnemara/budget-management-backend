from pydantic import BaseModel, conint, confloat, field_validator
from typing import Dict, List, Optional

class MonthlyTotalsIn(BaseModel):
    # Optional — if omitted or empty, we’ll just recompute all months from baseline (factor=1)
    month_totals: Dict[str, confloat(gt=0)] = {}

    @field_validator("month_totals")
    @classmethod
    def _keys_to_ints(cls, v: Dict[str, float]) -> Dict[int, float]:
        out: Dict[int, float] = {}
        for k, val in v.items():
            m = int(k)
            if m < 1 or m > 12:
                raise ValueError(f"Invalid month key: {k} (must be 1..12)")
            out[m] = float(val)
        return out  # type: ignore[return-value]

class MonthlyAllocationResult(BaseModel):
    month: conint(ge=1, le=12)
    rows_considered: int
    rows_written: int
    baseline_sum: float
    applied_factor: float
    skipped_zero_baseline: int

class MonthlyTotalsOut(BaseModel):
    results: List[MonthlyAllocationResult]
    overall_rows_considered: int
    overall_rows_written: int
    overall_baseline_sum: float
    months_requested: int
    months_with_allocation: int
    # optional nested payload in your brand->branch->months shape
    data: Optional[List[dict]] = None
