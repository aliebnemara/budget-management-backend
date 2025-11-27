"""
Budget V2 API Routes - Calculate Once, View Many Times
========================================================

These endpoints provide fast, pre-calculated budget effects data.

Endpoints:
- POST /api/v2/calculate-and-store-effects: Calculate and store all effects (triggered from Budget Setup)
- GET /api/v2/weekend-effect: Fast retrieval of weekend effect data
- GET /api/v2/islamic-calendar-effects: Fast retrieval of Islamic calendar effects data

Performance:
- V1 (calculate on demand): 3-5 seconds for single branch, 15-30 seconds for 40 branches
- V2 (retrieve stored): <1 second for any number of branches

Author: AI Development System
Created: 2025-11-27
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import traceback
from pydantic import BaseModel, Field

from src.api.routes.auth import get_current_user
from src.core.db import get_session, close_session
from src.services.effect_calculator_v2 import get_calculator_v2


# Router setup
budgetRouterV2 = APIRouter(prefix="/v2", tags=["budget_v2"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class CalculateEffectsRequest(BaseModel):
    """Request model for calculate and store endpoint"""
    branch_ids: List[int] = Field(..., description="List of branch IDs to calculate for")
    budget_year: int = Field(..., description="Target budget year (e.g., 2026)")
    compare_year: int = Field(..., description="Comparison year for historical data (e.g., 2025)")
    
    # Islamic calendar dates
    ramadan_CY: str = Field(..., description="Ramadan start date in compare year (YYYY-MM-DD)")
    ramadan_BY: str = Field(..., description="Ramadan start date in budget year (YYYY-MM-DD)")
    ramadan_daycount_CY: int = Field(30, description="Number of Ramadan days in compare year")
    ramadan_daycount_BY: int = Field(30, description="Number of Ramadan days in budget year")
    
    muharram_CY: str = Field(..., description="Muharram start date in compare year (YYYY-MM-DD)")
    muharram_BY: str = Field(..., description="Muharram start date in budget year (YYYY-MM-DD)")
    muharram_daycount_CY: int = Field(10, description="Number of Muharram days in compare year")
    muharram_daycount_BY: int = Field(10, description="Number of Muharram days in budget year")
    
    eid2_CY: str = Field(..., description="Eid Al-Adha date in compare year (YYYY-MM-DD)")
    eid2_BY: str = Field(..., description="Eid Al-Adha date in budget year (YYYY-MM-DD)")

class RetrieveEffectsRequest(BaseModel):
    """Request model for retrieve endpoints"""
    branch_ids: List[int] = Field(..., description="List of branch IDs to retrieve for")
    budget_year: int = Field(..., description="Budget year (e.g., 2026)")
    compare_year: int = Field(..., description="Comparison year (e.g., 2025)")
    months: Optional[List[int]] = Field(None, description="Optional list of specific months (1-12)")


# ============================================================
# API ENDPOINTS
# ============================================================

@budgetRouterV2.post("/calculate-and-store-effects", status_code=status.HTTP_200_OK)
def calculate_and_store_effects(
    request: CalculateEffectsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate and store all budget effects (weekend + Islamic calendar).
    
    This endpoint is triggered by the "Calculate & Store All Effects" button
    in the Budget Setup page.
    
    Process:
    1. Validates input parameters
    2. For each branch:
       - Calculates weekend/weekday effects (12 months)
       - Calculates Islamic calendar effects (Ramadan, Muharram, Eid)
       - Stores all results to database
    3. Returns summary of calculation results
    
    Expected duration: ~2.5 seconds per branch (e.g., 100 seconds for 40 branches)
    """
    session = get_session()
    try:
        # Get calculator instance
        calculator = get_calculator_v2(session)
        
        # Prepare Islamic dates dictionary
        islamic_dates = {
            'ramadan_CY': request.ramadan_CY,
            'ramadan_BY': request.ramadan_BY,
            'ramadan_daycount_CY': request.ramadan_daycount_CY,
            'ramadan_daycount_BY': request.ramadan_daycount_BY,
            'muharram_CY': request.muharram_CY,
            'muharram_BY': request.muharram_BY,
            'muharram_daycount_CY': request.muharram_daycount_CY,
            'muharram_daycount_BY': request.muharram_daycount_BY,
            'eid2_CY': request.eid2_CY,
            'eid2_BY': request.eid2_BY
        }
        
        # Calculate and store for all branches
        results = calculator.calculate_and_store_all_effects(
            branch_ids=request.branch_ids,
            budget_year=request.budget_year,
            compare_year=request.compare_year,
            islamic_dates=islamic_dates,
            user_id=current_user.get('id')
        )
        
        # Return success response
        return {
            'success': True,
            'message': f"Successfully calculated and stored effects for {results['summary']['total_branches']} branches",
            'results': results,
            'next_steps': {
                'weekend_effect_v2': '/weekend-effect-v2',
                'islamic_calendar_v2': '/islamic-calendar-v2'
            }
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate and store effects: {str(e)}"
        )
    finally:
        close_session(session)


@budgetRouterV2.post("/weekend-effect", status_code=status.HTTP_200_OK)
def get_weekend_effect_v2(
    request: RetrieveEffectsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Fast retrieval of pre-calculated weekend effect data.
    
    V1 Performance: 3-5 seconds (calculate on demand)
    V2 Performance: <1 second (retrieve stored data)
    
    For multiple branches, automatically aggregates the stored data.
    
    Response structure matches V1 API for compatibility:
    {
        'data': [
            {
                'month': 1,
                'monthName': 'January',
                'weekdayData': {
                    'Monday': {'count_compare': 5, 'sales_compare': 10000, ...},
                    ...
                }
            },
            ...
        ],
        'config': {'compare_year': 2025, 'budget_year': 2026}
    }
    """
    session = get_session()
    try:
        # Get calculator instance
        calculator = get_calculator_v2(session)
        
        # Retrieve stored data
        if len(request.branch_ids) == 1:
            # Single branch - direct retrieval
            branch_data = calculator.retrieve_effects(
                branch_ids=request.branch_ids,
                budget_year=request.budget_year,
                months=request.months
            )
            branch_id = request.branch_ids[0]
            monthly_effects = branch_data.get(branch_id, {})
        else:
            # Multiple branches - aggregate data
            monthly_effects = calculator.retrieve_aggregated_effects(
                branch_ids=request.branch_ids,
                budget_year=request.budget_year,
                months=request.months
            )
        
        # Check if any data was retrieved
        if not monthly_effects:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pre-calculated data found for budget year {request.budget_year}. Please run 'Calculate & Store All Effects' from the Home page first."
            )
        
        # Transform to V1-compatible format
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        data = []
        for month in range(1, 13):
            if month not in monthly_effects:
                continue
            
            month_data = monthly_effects[month]
            weekday_breakdown = month_data.get('weekday_breakdown', {})
            
            # Extract weekday pattern from breakdown
            weekday_data = weekday_breakdown.get('weekday_pattern', {})
            
            data.append({
                'month': month,
                'monthName': month_names[month - 1],
                'weekdayData': weekday_data,
                'effect_pct': month_data.get('weekday_effect_pct'),
                'calculated_at': month_data.get('calculated_at')
            })
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No calculated months found. Please run 'Calculate & Store All Effects' from the Home page first."
            )
        
        return {
            'data': data,
            'config': {
                'compare_year': request.compare_year,
                'budget_year': request.budget_year
            },
            'metadata': {
                'source': 'v2_stored_data',
                'branch_count': len(request.branch_ids),
                'is_aggregated': len(request.branch_ids) > 1
            }
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve weekend effect data: {str(e)}"
        )
    finally:
        close_session(session)


@budgetRouterV2.post("/islamic-calendar-effects", status_code=status.HTTP_200_OK)
def get_islamic_calendar_effects_v2(
    request: RetrieveEffectsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Fast retrieval of pre-calculated Islamic calendar effects data.
    
    V1 Performance: 5-8 seconds (calculate on demand)
    V2 Performance: <1 second (retrieve stored data)
    
    For multiple branches, automatically aggregates the stored data.
    
    Returns effects for all three Islamic calendar events:
    - Ramadan/Eid
    - Muharram
    - Eid Al-Adha
    
    Response structure matches V1 API for compatibility:
    {
        'data': [
            {
                'month': 1,
                'monthName': 'January',
                'ramadan_eid_pct': 5.23,
                'muharram_pct': -2.45,
                'eid2_pct': 3.12,
                'total_sales': 150000.00
            },
            ...
        ],
        'config': {...},
        'metadata': {...}
    }
    """
    session = get_session()
    try:
        # Get calculator instance
        calculator = get_calculator_v2(session)
        
        # Retrieve stored data
        if len(request.branch_ids) == 1:
            # Single branch - direct retrieval
            branch_data = calculator.retrieve_effects(
                branch_ids=request.branch_ids,
                budget_year=request.budget_year,
                months=request.months
            )
            branch_id = request.branch_ids[0]
            monthly_effects = branch_data.get(branch_id, {})
        else:
            # Multiple branches - aggregate data
            monthly_effects = calculator.retrieve_aggregated_effects(
                branch_ids=request.branch_ids,
                budget_year=request.budget_year,
                months=request.months
            )
        
        # Check if any data was retrieved
        if not monthly_effects:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pre-calculated data found for budget year {request.budget_year}. Please run 'Calculate & Store All Effects' from the Home page first."
            )
        
        # Debug logging for Islamic calendar
        print(f"🟢 Islamic Calendar V2: Retrieved data for {len(monthly_effects)} months")
        for month, data_item in list(monthly_effects.items())[:3]:  # Show first 3 months
            print(f"   Month {month}: Ramadan={data_item.get('ramadan_eid_pct')}, Muharram={data_item.get('muharram_pct')}, Eid2={data_item.get('eid2_pct')}")
        
        # Get branch and brand details from database to build V1-compatible structure
        from src.db.dbtables import Branch, Brand
        
        dbs = session
        brands_dict = {}
        
        # Build brand/branch structure
        for branch_id in request.branch_ids:
            branch = dbs.query(Branch).filter(Branch.id == branch_id).first()
            if not branch:
                continue
            
            brand_id = branch.brand_id
            brand = dbs.query(Brand).filter(Brand.id == brand_id).first()
            if not brand:
                continue
            
            # Initialize brand structure
            if brand_id not in brands_dict:
                brands_dict[brand_id] = {
                    'brand_id': brand_id,
                    'brand_name': brand.name,
                    'branches': {}
                }
            
            # Get monthly data for this branch (if multiple branches, use aggregated; if single, use individual)
            if len(request.branch_ids) == 1:
                branch_monthly_effects = monthly_effects
            else:
                # For aggregated case, all branches get the same aggregated data
                branch_monthly_effects = monthly_effects
            
            # Build months array
            months_array = []
            for month in range(1, 13):
                month_data = branch_monthly_effects.get(month, {})
                
                # Extract sales_CY from breakdown data (stored in daily_data)
                sales_CY = None
                ramadan_breakdown = month_data.get('ramadan_breakdown')
                muharram_breakdown = month_data.get('muharram_breakdown')
                eid2_breakdown = month_data.get('eid2_breakdown')
                
                # Try to get total sales from any available breakdown
                breakdown = ramadan_breakdown or muharram_breakdown or eid2_breakdown
                if breakdown and isinstance(breakdown, dict):
                    # Sum up sales_cy from all days in daily_data
                    daily_data = breakdown.get('daily_data', [])
                    if daily_data and isinstance(daily_data, list):
                        sales_CY = sum(day.get('sales_cy', 0) for day in daily_data if isinstance(day, dict))
                
                # Calculate estimated sales (apply percentage effects)
                ramadan_pct = month_data.get('ramadan_eid_pct')
                muharram_pct = month_data.get('muharram_pct')
                eid2_pct = month_data.get('eid2_pct')
                
                est_sales_no_ramadan = None
                est_sales_no_muharram = None
                est_sales_no_eid2 = None
                
                if sales_CY:
                    # Estimated sales if there was no Ramadan effect
                    if ramadan_pct is not None:
                        est_sales_no_ramadan = sales_CY / (1 + float(ramadan_pct) / 100)
                    
                    # Estimated sales if there was no Muharram effect
                    if muharram_pct is not None:
                        est_sales_no_muharram = sales_CY / (1 + float(muharram_pct) / 100)
                    
                    # Estimated sales if there was no Eid2 effect
                    if eid2_pct is not None:
                        est_sales_no_eid2 = sales_CY / (1 + float(eid2_pct) / 100)
                
                # Extract daily_sales array for frontend table display
                daily_sales = []
                if breakdown and isinstance(breakdown, dict):
                    daily_data = breakdown.get('daily_data', [])
                    if daily_data and isinstance(daily_data, list):
                        for day_item in daily_data:
                            if isinstance(day_item, dict):
                                daily_sales.append({
                                    'day': day_item.get('day'),
                                    'date': day_item.get('date_by'),  # 2026 date
                                    'actual': day_item.get('est_sales_by'),  # 2026 estimated sales (what frontend expects)
                                    'sales_cy': day_item.get('sales_cy'),  # 2025 historical sales (for reference)
                                    'estimated': day_item.get('est_sales_by')  # 2026 estimated sales (kept for compatibility)
                                })
                
                months_array.append({
                    'month': month,
                    'sales_CY': sales_CY,
                    'est_sales_no_ramadan': est_sales_no_ramadan,
                    'est_sales_no_muharram': est_sales_no_muharram,
                    'est_sales_no_eid2': est_sales_no_eid2,
                    'ramadan_eid_pct': month_data.get('ramadan_eid_pct'),
                    'muharram_pct': month_data.get('muharram_pct'),
                    'eid2_pct': month_data.get('eid2_pct'),
                    'calculated_at': month_data.get('calculated_at'),
                    'daily_sales': daily_sales  # ✅ Add daily breakdown for table display
                })
            
            # Add branch to brand
            brands_dict[brand_id]['branches'][branch_id] = {
                'branch_id': branch_id,
                'branch_name': branch.name,
                'months': months_array
            }
        
        # Convert to array format
        result_data = []
        for brand_id, brand_info in brands_dict.items():
            result_data.append({
                'brand_id': brand_info['brand_id'],
                'brand_name': brand_info['brand_name'],
                'branches': list(brand_info['branches'].values())
            })
        
        return {
            'data': result_data,
            'config': {
                'compare_year': request.compare_year,
                'budget_year': request.budget_year
            },
            'metadata': {
                'source': 'v2_stored_data',
                'branch_count': len(request.branch_ids),
                'is_aggregated': len(request.branch_ids) > 1
            }
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Islamic calendar effects: {str(e)}"
        )
    finally:
        close_session(session)


@budgetRouterV2.get("/last-calculation-timestamp", status_code=status.HTTP_200_OK)
def get_last_calculation_timestamp(
    budget_year: int = 2026,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the timestamp of the last calculation run.
    
    Returns the most recent calculated_at timestamp from the V2 table,
    along with elapsed time since the calculation.
    
    This allows the frontend to show "Last calculated: ..." message
    persistently across page refreshes.
    """
    session = get_session()
    try:
        from src.db.dbtables import BudgetEffectCalculationsV2
        from datetime import datetime, timezone
        
        # Get the most recent calculation timestamp
        latest_record = session.query(BudgetEffectCalculationsV2).filter(
            BudgetEffectCalculationsV2.budget_year == budget_year
        ).order_by(
            BudgetEffectCalculationsV2.calculated_at.desc()
        ).first()
        
        if not latest_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No calculations found for budget year {budget_year}"
            )
        
        # Calculate elapsed time
        calculated_at = latest_record.calculated_at
        if calculated_at.tzinfo is None:
            # If timestamp is naive, assume UTC
            calculated_at = calculated_at.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        elapsed = now - calculated_at
        elapsed_seconds = int(elapsed.total_seconds())
        
        return {
            'success': True,
            'budget_year': budget_year,
            'calculated_at': calculated_at.isoformat(),
            'elapsed_seconds': elapsed_seconds,
            'has_data': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve calculation timestamp: {str(e)}"
        )
    finally:
        close_session(session)


# Export router for inclusion in main app
__all__ = ['budgetRouterV2']
