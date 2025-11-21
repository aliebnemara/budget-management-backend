import csv
from io import TextIOWrapper, BytesIO
from typing import List, Tuple
from fastapi import UploadFile
import pandas as pd
from pathlib import Path

# Exact header expected (order + case must match)
EXPECTED_COLUMNS = [
    "OrderID",
    "OrderDateTime",
    "OrderType",
    "branch_id",
    "SubTotal",
    "VAT",
    "OrderDiscount",  # spelled as in your sample file
    "AmountDue",
    "guests",
    "ItemDiscount",
]

ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/octet-stream"  # Sometimes Excel files have this content type
}


def _is_empty(val) -> bool:
    return val is None or str(val).strip() == ""


def get_week_of_month(date):
    first_day = date.replace(day=1)
    # Shift weekday to 0=Monday, 6=Sunday
    adjusted_dom = date.day + first_day.weekday()
    return (adjusted_dom - 1) // 7 + 1


def _is_excel_file(filename: str) -> bool:
    """Check if file is an Excel file based on extension"""
    return filename.lower().endswith(('.xlsx', '.xls'))


def _read_file_to_dataframe(upload: UploadFile) -> Tuple[bool, pd.DataFrame | List[str]]:
    """
    Read uploaded file (CSV or Excel) into pandas DataFrame
    Returns (success, dataframe_or_errors)
    """
    try:
        filename = upload.filename or ""
        
        # Read Excel files
        if _is_excel_file(filename):
            try:
                # Read Excel file into DataFrame
                contents = upload.file.read()
                df = pd.read_excel(BytesIO(contents), engine='openpyxl')
                upload.file.seek(0)  # Reset for potential re-reading
                return True, df
            except Exception as e:
                return False, [f"Could not read Excel file: {str(e)}. Ensure it is a valid Excel file (.xlsx or .xls)."]
        
        # Read CSV files
        else:
            try:
                # TextIOWrapper handles UTF-8 and strips BOM via utf-8-sig
                text_stream = TextIOWrapper(
                    upload.file, encoding="utf-8-sig", newline="")
                df = pd.read_csv(text_stream)
                upload.file.seek(0)  # Reset for potential re-reading
                return True, df
            except Exception as e:
                return False, [f"Could not read CSV file: {str(e)}. Ensure it is valid and UTF-8 encoded."]
    
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"]


async def validate_sales_csv(upload: UploadFile) -> Tuple[bool, List[str] | str]:
    """
    Service function that performs all validation for CSV and Excel files.
    Returns (ok, result):
      - If ok is False: result is List[str] of human-readable errors
      - If ok is True: result is 'ok'
    """
    # Check content type (allow Excel files now)
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        filename = upload.filename or ""
        # Check by extension if content type doesn't match
        if not (filename.lower().endswith('.csv') or _is_excel_file(filename)):
            return False, ["Please upload a CSV or Excel file (.csv, .xlsx, .xls)."]
    
    # Read file into DataFrame
    success, result = _read_file_to_dataframe(upload)
    if not success:
        return False, result  # result contains error messages
    
    df = result  # result is DataFrame
    
    # Check if DataFrame is empty
    if df.empty or df.columns.tolist() == []:
        return False, ["File appears to have no header row or data."]
    
    # Get header from DataFrame
    header = df.columns.tolist()
    
    # Strict header check (order + case exact)
    if header != EXPECTED_COLUMNS:
        return False, [
            "File header does not match the required format.",
            f"Received header: {header}",
            f"Expected header: {EXPECTED_COLUMNS}",
            "Ensure column names (including case and spelling) and order are exactly the same.",
        ]
    
    errors: List[str] = []
    seen_order_ids = set()
    
    # Validate each row
    for idx, row in df.iterrows():
        # Skip completely empty rows
        if row.isna().all():
            continue
        
        row_index = idx + 2  # +2 because: idx starts at 0, and header is row 1
        
        order_id = str(row.get("OrderID", "")).strip() if pd.notna(row.get("OrderID")) else ""
        order_type = str(row.get("OrderType", "")).strip() if pd.notna(row.get("OrderType")) else ""
        branch_id = str(row.get("branch_id", "")).strip() if pd.notna(row.get("branch_id")) else ""
        
        # OrderID: required + unique
        if _is_empty(order_id):
            errors.append(f"Row {row_index}: OrderID is empty.")
        elif order_id in seen_order_ids:
            errors.append(f"Row {row_index}: Duplicate OrderID '{order_id}'.")
        else:
            seen_order_ids.add(order_id)
        
        # OrderType: required
        if _is_empty(order_type):
            errors.append(f"Row {row_index}: OrderType is empty.")
        
        # branch_id: required
        if _is_empty(branch_id):
            errors.append(f"Row {row_index}: branch_id is empty.")
    
    if errors:
        return False, errors
    
    # Process the data (same logic for both CSV and Excel)
    upload.file.seek(0)
    
    # Re-read with proper settings
    if _is_excel_file(upload.filename or ""):
        contents = upload.file.read()
        df = pd.read_excel(BytesIO(contents), engine='openpyxl')
    else:
        df = pd.read_csv(upload.file, encoding="utf-8-sig")
    
    df["OrderDateTime"] = pd.to_datetime(
        df["OrderDateTime"], dayfirst=True, format="mixed")
    # Create a mask for rows before 6 AM
    before_cutoff = df["OrderDateTime"].dt.time < (
        pd.Timestamp("06:00:00").time())
    # Subtract a day where condition is True, else keep the date
    df["business_date"] = df["OrderDateTime"].dt.normalize(
    ) - pd.to_timedelta(before_cutoff.astype(int), unit="D")
    df["ItemDiscount"] = df["ItemDiscount"].fillna(0)
    df["guests"] = df["guests"].fillna(0)
    order_type_map = {
        1: 'Delivery',
        2: 'Takeaway',
        4: 'Drive Thru',
        6: 'Catering',
        7: 'Staff Meal'
    }
    # Apply mapping with default value 'Dinein'
    df['OrderType'] = df['OrderType'].map(order_type_map).fillna('Dinein')
    df["day_of_week"] = df["business_date"].dt.day_name()
    df["week_of_month"] = df["business_date"].apply(get_week_of_month)
    df["Discount"] = df["OrderDiscount"]+df["ItemDiscount"]
    df["gross"] = df["AmountDue"]+df["Discount"]
    df.drop(["OrderDateTime", "OrderDiscount",
            "ItemDiscount", "SubTotal"], axis=1, inplace=True)
    # ---------- Append to BaseData.pkl, skipping existing OrderIDs ----------
    BASE_DIR = Path(__file__).resolve().parents[2]
    pickle_path = BASE_DIR / "BaseData.pkl"
    added=0
    skipped=0
    if pickle_path.exists():
        try:
            existing = pd.read_pickle(pickle_path)
            # existing["OrderID"] = existing["OrderID"].astype("string")
            # df["OrderID"] = df["OrderID"].astype("string")
            new_only = df[~df["OrderID"].isin(existing["OrderID"])]
            added = len(new_only)
            skipped = len(df) - added
            combined = pd.concat([existing, new_only], ignore_index=True)
        except Exception as e:
            # If the pickle is unreadable/corrupt, we just start fresh
            # combined = df.copy()
            return False, "File is Corrupt"
    else:
        return False, "Base file doesn't exist"

    combined.to_pickle(pickle_path)
    return True, "ok"
