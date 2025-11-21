from typing import Optional
from fastapi import APIRouter, File, Query, UploadFile, status, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from src.models.branch_list import BranchListOut
import pandas as pd
from io import BytesIO
from src.models.budget import defaultBudgetModel
from src.models.projection import ProjectionEstimateIn, ProjectionInputModel
from src.models.projected_allocation_branch import BranchTotalsIn, BranchTotalsOut
from src.models.projected_allocation_branch_monthly import BranchMonthlyTotalsIn, BranchMonthlyTotalsOut
from src.services.budget import calculateDefault
from src.services.saveProjections import upsert_projection_estimate, upsert_projection_input
from src.services.budget_state import compute_or_reuse
import traceback
from src.models.projection_est_adjust import AllocateGrandTotalIn, AllocateGrandTotalOut
from src.services.projected_allocation import allocate_grand_total
from src.models.projected_allocation_monthly import MonthlyTotalsIn, MonthlyTotalsOut
from src.services.allocation_service_monthly import allocate_monthly_totals
from src.services.allocation_service_branch import allocate_branch_totals
from src.services.allocation_service_branch_monthly import allocate_branch_monthly_totals
from src.services.branch_service import list_branches
from src.services.importdata import validate_sales_csv

budgetRouter = APIRouter(prefix="/api")

# Import authentication dependency
from src.api.routes.auth import get_current_user


def filter_budget_data_by_permissions(data: dict, user: dict) -> dict:
    """Filter budget data based on user's brand and branch permissions"""
    # Check if user is super_admin (has access to all data)
    is_super_admin = any(role.get("name") == "super_admin" for role in user.get("roles", []))
    
    if is_super_admin:
        # Super admin sees all data
        return data
    
    # Get user's brand and branch access
    user_brand_ids = user.get("brand_access", [])
    user_branch_ids = user.get("branch_access", [])
    
    # If user has no restrictions, return all data
    if not user_brand_ids and not user_branch_ids:
        return data
    
    # Filter the data
    filtered_data = data.copy()
    
    # Filter brands if data has a 'data' key with brands
    if "data" in filtered_data and isinstance(filtered_data["data"], list):
        filtered_brands = []
        
        for brand in filtered_data["data"]:
            brand_id = brand.get("brand_id")
            
            # Check if user has access to this brand
            if user_brand_ids and brand_id not in user_brand_ids:
                continue  # Skip this brand
            
            # Filter branches within the brand
            if user_branch_ids and "branches" in brand:
                filtered_branches_list = [
                    branch for branch in brand["branches"]
                    if branch.get("branch_id") in user_branch_ids
                ]
                
                # Only include brand if it has accessible branches
                if filtered_branches_list:
                    filtered_brand = brand.copy()
                    filtered_brand["branches"] = filtered_branches_list
                    filtered_brands.append(filtered_brand)
            else:
                # No branch filtering needed, include whole brand
                filtered_brands.append(brand)
        
        filtered_data["data"] = filtered_brands
    
    return filtered_data




@budgetRouter.post("/calculatedefault", status_code=status.HTTP_202_ACCEPTED)
def defaultCalculation(request: defaultBudgetModel, current_user: dict = Depends(get_current_user)):
    try:
        # res=calculateDefault(request)
        # return {"Data":res}
        result = compute_or_reuse(request, recompute=calculateDefault)
        # Filter results based on user permissions
        return filter_budget_data_by_permissions(result, current_user)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@budgetRouter.post("/home", status_code=status.HTTP_202_ACCEPTED)
def defaultCalculationHome(current_user: dict = Depends(get_current_user)):
    try:
        # res=calculateDefault(request)
        # return {"Data":res}
        result = compute_or_reuse(None, recompute=calculateDefault)
        # Filter results based on user permissions
        return filter_budget_data_by_permissions(result, current_user)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@budgetRouter.post("/projection-inputs/upsert")
def upsert_projection(body: ProjectionInputModel):
    upsert_projection_input(body.model_dump())
    return {"status": "ok"}


@budgetRouter.post("/pre-estimation/upsert")
def upsert_estimate(body: ProjectionEstimateIn):
    try:
        res = upsert_projection_estimate(body.model_dump())
        return {"ok": True, **res}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="Failed to upsert projection estimate")


@budgetRouter.post("/allocate-grand-total", response_model=AllocateGrandTotalOut)
def allocate_total_sales(payload: AllocateGrandTotalIn, include_data: bool = True, current_user: dict = Depends(get_current_user)):
    """
    POST /allocation/grand-total?include_data=true
    Body: { "grand_total_estimated_sales": 10000000 }
    Returns:
      - summary (factor, counts…)
      - and, when include_data=true, "data": [ { brand_id, brand_name, branches: [...] } ]
        Each months[] object includes your existing fields PLUS est_* from projection_estimate_adjusted.
    """
    try:
        result = allocate_grand_total(payload, include_data=True)
        return filter_budget_data_by_permissions(result, current_user)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Allocation failed")


@budgetRouter.post("/allocation-monthly-totals", response_model=MonthlyTotalsOut)
def allocate_monthly(payload: MonthlyTotalsIn, include_data: bool = True, current_user: dict = Depends(get_current_user)):
    """
    POST /allocation-monthly-totals?include_data=true
    Body:
    {
      "month_totals": {
        "1": 1000000,
        "2": 900000,
        "3": 950000
      }
    }
    - Only the provided months are re-allocated.
    - Each month uses its own factor based on that month’s baseline sum.
    - Results upsert into projection_estimate_adjusted.
    - When include_data=true, returns the nested data array.
    """
    try:
        result = allocate_monthly_totals(payload, include_data=include_data)
        return filter_budget_data_by_permissions(result, current_user)
    except Exception:
        raise HTTPException(
            status_code=500, detail="Monthly allocation failed")


@budgetRouter.post("/branch-totals", response_model=BranchTotalsOut)
def allocate_branch_totals_api(payload: BranchTotalsIn, include_data: bool = True, current_user: dict = Depends(get_current_user)):
    """
    POST /allocation/branch-totals?include_data=true
    Body: {"branch_totals": {"189": 1200000, "190": null}}
      - 189 scaled to 1.2M across all months
      - 190 copied from baseline (factor=1)
      - Any branch not mentioned is also copied from baseline (factor=1)
    """
    try:
        result = allocate_branch_totals(payload, include_data=include_data)
        return filter_budget_data_by_permissions(result, current_user)
    except Exception:
        raise HTTPException(
            status_code=500, detail="Branch grand-total allocation failed")


@budgetRouter.post("/branch-monthly-totals", response_model=BranchMonthlyTotalsOut)
def allocate_branch_monthly_totals_api(payload: BranchMonthlyTotalsIn, include_data: bool = True, current_user: dict = Depends(get_current_user)):
    """
    POST /allocation/branch-monthly-totals?include_data=true
    Body:
    {
      "branch_month_totals": {
        "189": {"1": 100000, "2": 120000, "3": null},
        "190": {"1": 90000}
      }
    }
    - Provided (branch, month) with value -> scaled to that total
    - Provided (branch, month) with null/<=0 -> copied from baseline (factor=1)
    - Any (branch, month) not provided -> copied from baseline (factor=1)
    """
    try:
        result = allocate_branch_monthly_totals(payload, include_data=include_data)
        return filter_budget_data_by_permissions(result, current_user)
    except Exception:
        raise HTTPException(
            status_code=500, detail="Branch monthly allocation failed")
    
@budgetRouter.get("/branches", response_model=BranchListOut)
def get_branches(brand_id: Optional[int] = Query(None, description="Filter by brand id")):
    """
    GET /branches
    GET /branches?brand_id=38

    Returns:
      {
        "branches": [
          { "branch_id": 189, "branch_name": "AL ABRAAJ SEHLA", "brand_id": 38, "brand_name": "AL ABRAAJ RESTAURANTS" },
          ...
        ]
      }
    """
    try:
        data = list_branches(brand_id=brand_id)
        return {"branches": data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list branches")

@budgetRouter.post("/import-sales")
async def import_sales(file: UploadFile = File(...)):
    """
    Validates and imports uploaded sales data (CSV or Excel format) for:
    - exact header (order + case)
    - non-empty, unique OrderID
    - non-empty OrderType
    - non-empty branch_id
    
    Supported formats: .csv, .xlsx, .xls
    Returns human-readable errors or 'ok' if valid.
    """
    ok, errors_or_msg = await validate_sales_csv(file)

    if not ok:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "File validation failed. Please fix the issues below and try again.",
                "errors": errors_or_msg,
            },
        )

    return {"status": "ok", "message": "Sales data imported successfully."}

@budgetRouter.get("/download-sales-template")
async def download_sales_template():
    """
    Download master Excel template for sales data import.
    
    Returns an Excel file with:
    - Correct column headers in exact order
    - Sample data rows to demonstrate format
    - Professional formatting with colors and borders
    """
    # Define the expected columns
    columns = [
        "OrderID",
        "OrderDateTime",
        "OrderType",
        "branch_id",
        "SubTotal",
        "VAT",
        "OrderDiscount",
        "AmountDue",
        "guests",
        "ItemDiscount",
    ]
    
    # Create sample data (3 example rows)
    sample_data = [
        {
            "OrderID": "ORD001",
            "OrderDateTime": "01/01/2025 14:30",
            "OrderType": "Dinein",
            "branch_id": "189",
            "SubTotal": 45.50,
            "VAT": 2.28,
            "OrderDiscount": 0.00,
            "AmountDue": 47.78,
            "guests": 3,
            "ItemDiscount": 0.00
        },
        {
            "OrderID": "ORD002",
            "OrderDateTime": "01/01/2025 15:45",
            "OrderType": "1",
            "branch_id": "190",
            "SubTotal": 32.00,
            "VAT": 1.60,
            "OrderDiscount": 2.00,
            "AmountDue": 31.60,
            "guests": 0,
            "ItemDiscount": 0.50
        },
        {
            "OrderID": "ORD003",
            "OrderDateTime": "02/01/2025 12:15",
            "OrderType": "2",
            "branch_id": "189",
            "SubTotal": 28.75,
            "VAT": 1.44,
            "OrderDiscount": 0.00,
            "AmountDue": 30.19,
            "guests": 0,
            "ItemDiscount": 0.00
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_data, columns=columns)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales Data')
        
        # Get workbook and worksheet for styling
        workbook = writer.book
        worksheet = writer.sheets['Sales Data']
        
        # Apply professional styling
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
        
        # Header styling
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Data styling
        border = Border(
            left=Side(style='thin', color='D0D0D0'),
            right=Side(style='thin', color='D0D0D0'),
            top=Side(style='thin', color='D0D0D0'),
            bottom=Side(style='thin', color='D0D0D0')
        )
        data_alignment = Alignment(horizontal="left", vertical="center")
        
        # Style header row
        for col_num, column in enumerate(columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border
            # Set column width
            worksheet.column_dimensions[cell.column_letter].width = 15
        
        # Style data rows with alternating colors
        for row_num in range(2, len(sample_data) + 2):
            fill_color = "F2F2F2" if row_num % 2 == 0 else "FFFFFF"
            row_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            
            for col_num in range(1, len(columns) + 1):
                cell = worksheet.cell(row=row_num, column=col_num)
                cell.fill = row_fill
                cell.border = border
                cell.alignment = data_alignment
        
        # Add instructions sheet
        instructions_data = {
            "Field": columns,
            "Description": [
                "Unique order identifier (required, must be unique)",
                "Date and time of order (format: DD/MM/YYYY HH:MM)",
                "Order type: Dinein, 1=Delivery, 2=Takeaway, 4=Drive Thru, 6=Catering, 7=Staff Meal",
                "Branch ID number (required)",
                "Subtotal amount before tax and discounts",
                "VAT/Tax amount",
                "Order-level discount amount",
                "Final amount due after all calculations",
                "Number of guests (0 for non-dine-in orders)",
                "Item-level discount amount"
            ],
            "Required": [
                "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "No", "No"
            ]
        }
        instructions_df = pd.DataFrame(instructions_data)
        instructions_df.to_excel(writer, index=False, sheet_name='Instructions')
        
        # Style instructions sheet
        inst_worksheet = writer.sheets['Instructions']
        for col_num in range(1, 4):
            cell = inst_worksheet.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border
        
        # Set column widths for instructions
        inst_worksheet.column_dimensions['A'].width = 20
        inst_worksheet.column_dimensions['B'].width = 70
        inst_worksheet.column_dimensions['C'].width = 12
        
        # Style instructions data rows
        for row_num in range(2, len(columns) + 2):
            for col_num in range(1, 4):
                cell = inst_worksheet.cell(row=row_num, column=col_num)
                cell.border = border
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    
    output.seek(0)
    
    # Return as downloadable file
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=Sales_Import_Template.xlsx"
        }
    )