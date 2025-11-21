from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import date
from src.core.db import get_session, close_session
from src.api.routes.auth import get_current_user
from src.services.daily_sales_service import get_daily_sales_pivot, export_daily_sales_to_excel
from src.models.daily_sales import DailySalesResponse
import io

dailySalesRouter = APIRouter(prefix="/api/daily-sales", tags=["daily-sales"])


@dailySalesRouter.get("/", response_model=DailySalesResponse)
def get_daily_sales(
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    brand_ids: Optional[List[int]] = Query(None, description="Filter by brand IDs (comma-separated)"),
    branch_ids: Optional[List[int]] = Query(None, description="Filter by branch IDs (comma-separated)"),
    view_by: str = Query("day", description="Aggregation level: day, week, month, quarter, year"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get daily sales data in pivot table format.
    
    Returns:
    - Each row represents one business date
    - Columns contain metrics (gross, net, VAT, discount, transactions, guests)
    - Metrics are broken down by service type: Total, Dine-in, Delivery, Takeaway, Drive Thru, Catering
    
    Query Parameters:
    - start_date: Filter sales from this date onwards (inclusive)
    - end_date: Filter sales up to this date (inclusive)
    - brand_ids: Filter by specific brands (filters all branches of those brands)
    - branch_ids: Filter by specific branches
    
    Authentication:
    - Requires valid JWT token in Authorization header
    """
    dbs = get_session()
    
    try:
        # Call service to get pivot data
        result = get_daily_sales_pivot(
            db=dbs,
            start_date=start_date,
            end_date=end_date,
            brand_ids=brand_ids,
            branch_ids=branch_ids,
            view_by=view_by
        )
        
        return result
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="BaseData.pkl file not found. Please ensure data file exists."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving daily sales data: {str(e)}"
        )
    finally:
        close_session(dbs)


@dailySalesRouter.get("/export")
def export_daily_sales(
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    brand_ids: Optional[List[int]] = Query(None, description="Filter by brand IDs (comma-separated)"),
    branch_ids: Optional[List[int]] = Query(None, description="Filter by branch IDs (comma-separated)"),
    view_by: str = Query("day", description="Aggregation level: day, week, month, quarter, year"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export daily sales data to Excel file.
    
    Returns an Excel file (.xlsx) with the filtered pivot table data.
    Same filters as the main endpoint.
    
    Authentication:
    - Requires valid JWT token in Authorization header
    """
    dbs = get_session()
    
    try:
        # Get the pivot data
        result = get_daily_sales_pivot(
            db=dbs,
            start_date=start_date,
            end_date=end_date,
            brand_ids=brand_ids,
            branch_ids=branch_ids,
            view_by=view_by
        )
        
        # Convert to Excel
        excel_buffer = export_daily_sales_to_excel(result)
        
        # Generate filename
        filename_parts = ["daily_sales"]
        if start_date:
            filename_parts.append(f"from_{start_date}")
        if end_date:
            filename_parts.append(f"to_{end_date}")
        if brand_ids:
            filename_parts.append(f"brands_{'-'.join(map(str, brand_ids))}")
        if branch_ids:
            filename_parts.append(f"branches_{'-'.join(map(str, branch_ids))}")
        filename_parts.append(f"by_{view_by}")
        
        filename = "_".join(filename_parts) + ".xlsx"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="BaseData.pkl file not found. Please ensure data file exists."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting daily sales data: {str(e)}"
        )
    finally:
        close_session(dbs)
