from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class ServiceTypeMetrics(BaseModel):
    """Metrics for a specific service type"""
    gross: float = Field(default=0.0, description="Gross sales amount")
    net: float = Field(default=0.0, description="Net sales amount (AmountDue)")
    vat: float = Field(default=0.0, description="VAT amount")
    discount: float = Field(default=0.0, description="Discount amount")
    transactions: int = Field(default=0, description="Number of transactions")
    guests: Optional[int] = Field(default=None, description="Number of guests (only for Dinein)")


class DailySalesRow(BaseModel):
    """Single row in the pivot table representing one business date"""
    business_date: date
    period_label: Optional[str] = Field(default=None, description="Display label for the period (e.g., 'Week 1, 2025')")
    
    # Total metrics (all service types combined)
    total_gross: float
    total_net: float
    total_vat: float
    total_discount: float
    total_transactions: int
    total_guests: int
    total_avg_check: float = Field(description="Average check: gross / transactions")
    
    # Dine-in metrics (includes guests)
    dinein_gross: float
    dinein_net: float
    dinein_vat: float
    dinein_discount: float
    dinein_transactions: int
    dinein_guests: int
    dinein_avg_check: float = Field(description="Average check: gross / transactions")
    dinein_avg_by_guest: float = Field(description="Average per guest: gross / guests")
    
    # Delivery metrics (no guests)
    delivery_gross: float
    delivery_net: float
    delivery_vat: float
    delivery_discount: float
    delivery_transactions: int
    delivery_avg_check: float = Field(description="Average check: gross / transactions")
    
    # Takeaway metrics (no guests)
    takeaway_gross: float
    takeaway_net: float
    takeaway_vat: float
    takeaway_discount: float
    takeaway_transactions: int
    takeaway_avg_check: float = Field(description="Average check: gross / transactions")
    
    # Drive Thru metrics (no guests)
    drivethru_gross: float
    drivethru_net: float
    drivethru_vat: float
    drivethru_discount: float
    drivethru_transactions: int
    drivethru_avg_check: float = Field(description="Average check: gross / transactions")
    
    # Catering metrics (no guests)
    catering_gross: float
    catering_net: float
    catering_vat: float
    catering_discount: float
    catering_transactions: int
    catering_avg_check: float = Field(description="Average check: gross / transactions")


class DailySalesResponse(BaseModel):
    """API response for daily sales pivot table"""
    data: list[DailySalesRow]
    total_rows: int
    date_range: dict[str, Optional[str]] = Field(
        description="Applied date range filter",
        example={"start_date": "2025-10-01", "end_date": "2025-10-31"}
    )
    filters: dict[str, Optional[int] | Optional[list[int]]] = Field(
        description="Applied filters (can be single int or list of ints)",
        example={"brand_ids": [1, 2, 3], "branch_ids": [5, 6]}
    )
