from pydantic import BaseModel, condecimal
from typing import Optional

DecPct = Optional[condecimal(max_digits=8, decimal_places=4)]
DecVal = Optional[condecimal(max_digits=14, decimal_places=4)]

class ProjectionInputModel(BaseModel):
    branch_id: int
    month: int

    dining_sales_pct: DecPct = None
    projected_dinin_avg_check: DecVal = None
    projected_avg_per_cover: DecVal = None
    projected_guest_count_new: DecVal = None

    delivery_sales_pct: DecPct = None
    projected_delivery_avg_check: DecVal = None

    takeaway_sales_pct: DecPct = None
    projected_takeaway_avg_check: DecVal = None

    drivethru_sales_pct: DecPct = None
    projected_drivethru_avg_check: DecVal = None

    catering_trans_pct: DecPct = None
    projected_catering_avg_check: DecVal = None

    projected_discount_pct: DecPct = None
    marketing_activities_pct: DecPct = None

    projected_delivery_sales_new: DecVal = None
    projected_delivery_trans_new: DecVal = None
    projected_dinein_sales_new: DecVal = None
    projected_dinein_trans_new: DecVal = None
    projected_takeaway_sales_new: DecVal = None
    projected_takeaway_trans_new: DecVal = None
    projected_drivethru_sales_new: DecVal = None
    projected_drivethru_trans_new: DecVal = None
    projected_catering_sales_new: DecVal = None
    projected_catering_trans_new: DecVal = None

class ProjectionEstimateIn(BaseModel):
    branch_id: int
    month: int

    est_dine_sales: Optional[float] = None
    est_dine_trans: Optional[float] = None
    est_customer_count: Optional[float] = None
    est_dine_avg_check: Optional[float] = None
    est_avg_per_cover: Optional[float] = None

    est_delivery_sales: Optional[float] = None
    est_delivery_trans: Optional[float] = None
    est_delivery_avg_check: Optional[float] = None

    est_takeway_sales: Optional[float] = None
    est_takeway_trans: Optional[float] = None
    est_takeway_avg_check: Optional[float] = None

    est_drivethru_sales: Optional[float] = None
    est_drivethru_trans: Optional[float] = None
    est_drivethru_avg_check: Optional[float] = None

    est_catering_sales: Optional[float] = None
    est_catering_trans: Optional[float] = None
    est_catering_avg_check: Optional[float] = None

    est_total_sales: Optional[float] = None
    est_total_trans: Optional[float] = None
    est_total_avg: Optional[float] = None
    est_total_discount: Optional[float] = None
    est_discount_pct: Optional[float] = None
    est_vat: Optional[float] = None
    est_net_sales: Optional[float] = None

