"""
Daily Sales Service
Provides pivot table aggregation from BaseData.pkl
Date as rows, metrics as columns broken down by service type
"""

import pandas as pd
from datetime import date
from typing import Optional, List
from sqlalchemy.orm import Session
from src.db.dbtables import Brand, Branch
from src.models.daily_sales import DailySalesRow, DailySalesResponse
import io

# Path to the BaseData pickle file
BASE_DATA_PATH = "/home/user/backend/Backend/BaseData.pkl"


def get_daily_sales_pivot(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    brand_ids: Optional[List[int]] = None,
    branch_ids: Optional[List[int]] = None,
    view_by: str = "day"
) -> DailySalesResponse:
    """
    Get daily sales in pivot format: Date as rows, metrics as columns
    
    Args:
        db: Database session
        start_date: Filter by start date (inclusive)
        end_date: Filter by end date (inclusive)
        brand_ids: Filter by brand IDs (list)
        branch_ids: Filter by branch IDs (list)
    
    Returns:
        DailySalesResponse with pivot table data
    """
    
    # Load BaseData
    df = pd.read_pickle(BASE_DATA_PATH)
    
    # Ensure business_date is datetime type
    df['business_date'] = pd.to_datetime(df['business_date'])
    
    # Apply filters
    if start_date:
        df = df[df['business_date'] >= pd.Timestamp(start_date)]
    
    if end_date:
        df = df[df['business_date'] <= pd.Timestamp(end_date)]
    
    if brand_ids and len(brand_ids) > 0:
        # Get all branches for these brands
        branches = db.query(Branch).filter(
            Branch.brand_id.in_(brand_ids),
            Branch.is_deleted == False
        ).all()
        branch_ids_from_brands = [b.id for b in branches]
        if branch_ids_from_brands:
            df = df[df['branch_id'].isin(branch_ids_from_brands)]
        else:
            # No branches found, return empty
            return DailySalesResponse(
                data=[],
                total_rows=0,
                date_range={
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                filters={"brand_ids": brand_ids, "branch_ids": branch_ids}
            )
    
    if branch_ids and len(branch_ids) > 0:
        df = df[df['branch_id'].isin(branch_ids)]
    
    # Check if dataframe is empty
    if df.empty:
        return DailySalesResponse(
            data=[],
            total_rows=0,
            date_range={
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            filters={"brand_ids": brand_ids, "branch_ids": branch_ids}
        )
    
    # Calculate net (gross - discount)
    df['net'] = df['gross'] - df['Discount']
    
    # Add period columns based on view_by parameter
    # All aggregations use proper period keys to prevent duplicates
    if view_by == "week":
        # US Week: Sunday as first day of week (week starts on Sunday)
        # Calculate the Sunday of each week
        # weekday: Monday=0, Tuesday=1, ..., Saturday=5, Sunday=6
        # To get Sunday: if weekday=6 (Sunday), subtract 0; otherwise subtract (weekday+1)
        days_since_sunday = (df['business_date'].dt.weekday + 1) % 7
        df['period'] = df['business_date'] - pd.to_timedelta(days_since_sunday, unit='d')
        
        # Create week labels using US week numbering (Sunday start, %U format)
        # CRITICAL: Use period (Sunday) for label to ensure all dates in same week get same label
        # Remove leading zeros from week numbers (01 → 1, 02 → 2, etc.) by converting to int
        df['period_label'] = 'Week ' + df['period'].dt.strftime('%U').astype(int).astype(str) + ', ' + df['period'].dt.strftime('%Y')
    elif view_by == "month":
        # Month: Use first day of month as period key
        # Creates unique period for each month (2025-01-01, 2025-02-01, etc.)
        df['period'] = pd.to_datetime(
            df['business_date'].dt.year.astype(str) + '-' +
            df['business_date'].dt.month.astype(str).str.zfill(2) + '-01'
        )
        # User-friendly label: "January 2025", "February 2025"
        # Use period (first day of month) for consistency
        df['period_label'] = df['period'].dt.strftime('%B %Y')
    elif view_by == "quarter":
        # Quarter: Use first day of quarter as period key
        # Q1 = Jan 1, Q2 = Apr 1, Q3 = Jul 1, Q4 = Oct 1
        quarter_month = ((df['business_date'].dt.quarter - 1) * 3 + 1).astype(str).str.zfill(2)
        df['period'] = pd.to_datetime(
            df['business_date'].dt.year.astype(str) + '-' + quarter_month + '-01'
        )
        # User-friendly label: "2025Q1", "2025Q2"
        # Use period (first day of quarter) for consistency
        df['period_label'] = df['period'].dt.year.astype(str) + 'Q' + df['period'].dt.quarter.astype(str)
    elif view_by == "year":
        # Year: Use first day of year as period key (2025-01-01, 2024-01-01)
        df['period'] = pd.to_datetime(df['business_date'].dt.year.astype(str) + '-01-01')
        # User-friendly label: "2025", "2024"
        # Use period (first day of year) for consistency
        df['period_label'] = df['period'].dt.year.astype(str)
    else:  # day (default)
        # Day: Each date is its own period
        df['period'] = df['business_date']
        df['period_label'] = df['business_date'].dt.strftime('%Y-%m-%d')
    
    # Aggregate by period and OrderType
    agg_dict = {
        'gross': 'sum',
        'net': 'sum',
        'VAT': 'sum',
        'Discount': 'sum',
        'OrderID': 'count',  # transactions
        'guests': 'sum'
    }
    
    grouped = df.groupby(['period', 'OrderType']).agg(agg_dict).reset_index()
    grouped.rename(columns={'OrderID': 'transactions'}, inplace=True)
    
    # Create a period_label lookup from the original dataframe
    period_labels = df[['period', 'period_label']].drop_duplicates().set_index('period')['period_label'].to_dict()
    
    # Pivot: periods as rows, service types as columns
    pivot_data = {}
    
    # Get unique periods
    unique_periods = sorted(grouped['period'].unique())
    
    for period in unique_periods:
        period_data = grouped[grouped['period'] == period]
        
        # Initialize row with zeros
        row = {
            'business_date': period.date(),
            'period_label': period_labels.get(period),  # Add the period label
            # Total (will be calculated)
            'total_gross': 0.0,
            'total_net': 0.0,
            'total_vat': 0.0,
            'total_discount': 0.0,
            'total_transactions': 0,
            'total_guests': 0,
            'total_avg_check': 0.0,
            # Dinein
            'dinein_gross': 0.0,
            'dinein_net': 0.0,
            'dinein_vat': 0.0,
            'dinein_discount': 0.0,
            'dinein_transactions': 0,
            'dinein_guests': 0,
            'dinein_avg_check': 0.0,
            'dinein_avg_by_guest': 0.0,
            # Delivery
            'delivery_gross': 0.0,
            'delivery_net': 0.0,
            'delivery_vat': 0.0,
            'delivery_discount': 0.0,
            'delivery_transactions': 0,
            'delivery_avg_check': 0.0,
            # Takeaway
            'takeaway_gross': 0.0,
            'takeaway_net': 0.0,
            'takeaway_vat': 0.0,
            'takeaway_discount': 0.0,
            'takeaway_transactions': 0,
            'takeaway_avg_check': 0.0,
            # Drive Thru
            'drivethru_gross': 0.0,
            'drivethru_net': 0.0,
            'drivethru_vat': 0.0,
            'drivethru_discount': 0.0,
            'drivethru_transactions': 0,
            'drivethru_avg_check': 0.0,
            # Catering
            'catering_gross': 0.0,
            'catering_net': 0.0,
            'catering_vat': 0.0,
            'catering_discount': 0.0,
            'catering_transactions': 0,
            'catering_avg_check': 0.0,
        }
        
        # Fill in data for each service type
        for _, order_type_row in period_data.iterrows():
            order_type = order_type_row['OrderType']
            gross = float(order_type_row['gross'])
            net = float(order_type_row['net'])
            vat = float(order_type_row['VAT'])
            discount = float(order_type_row['Discount'])
            transactions = int(order_type_row['transactions'])
            guests = int(order_type_row['guests']) if pd.notna(order_type_row['guests']) else 0
            
            # Map to correct fields
            if order_type == 'Dinein':
                row['dinein_gross'] = gross
                row['dinein_net'] = net
                row['dinein_vat'] = vat
                row['dinein_discount'] = discount
                row['dinein_transactions'] = transactions
                row['dinein_guests'] = guests
            elif order_type == 'Delivery':
                row['delivery_gross'] = gross
                row['delivery_net'] = net
                row['delivery_vat'] = vat
                row['delivery_discount'] = discount
                row['delivery_transactions'] = transactions
            elif order_type == 'Takeaway':
                row['takeaway_gross'] = gross
                row['takeaway_net'] = net
                row['takeaway_vat'] = vat
                row['takeaway_discount'] = discount
                row['takeaway_transactions'] = transactions
            elif order_type == 'Drive Thru':
                row['drivethru_gross'] = gross
                row['drivethru_net'] = net
                row['drivethru_vat'] = vat
                row['drivethru_discount'] = discount
                row['drivethru_transactions'] = transactions
            elif order_type == 'Catering':
                row['catering_gross'] = gross
                row['catering_net'] = net
                row['catering_vat'] = vat
                row['catering_discount'] = discount
                row['catering_transactions'] = transactions
        
        # Calculate totals
        row['total_gross'] = (row['dinein_gross'] + row['delivery_gross'] + 
                             row['takeaway_gross'] + row['drivethru_gross'] + row['catering_gross'])
        row['total_net'] = (row['dinein_net'] + row['delivery_net'] + 
                           row['takeaway_net'] + row['drivethru_net'] + row['catering_net'])
        row['total_vat'] = (row['dinein_vat'] + row['delivery_vat'] + 
                           row['takeaway_vat'] + row['drivethru_vat'] + row['catering_vat'])
        row['total_discount'] = (row['dinein_discount'] + row['delivery_discount'] + 
                                row['takeaway_discount'] + row['drivethru_discount'] + row['catering_discount'])
        row['total_transactions'] = (row['dinein_transactions'] + row['delivery_transactions'] + 
                                     row['takeaway_transactions'] + row['drivethru_transactions'] + row['catering_transactions'])
        row['total_guests'] = row['dinein_guests']  # Only dinein has guests
        
        # Calculate average checks (gross / transactions)
        row['total_avg_check'] = row['total_gross'] / row['total_transactions'] if row['total_transactions'] > 0 else 0.0
        row['dinein_avg_check'] = row['dinein_gross'] / row['dinein_transactions'] if row['dinein_transactions'] > 0 else 0.0
        row['dinein_avg_by_guest'] = row['dinein_gross'] / row['dinein_guests'] if row['dinein_guests'] > 0 else 0.0
        row['delivery_avg_check'] = row['delivery_gross'] / row['delivery_transactions'] if row['delivery_transactions'] > 0 else 0.0
        row['takeaway_avg_check'] = row['takeaway_gross'] / row['takeaway_transactions'] if row['takeaway_transactions'] > 0 else 0.0
        row['drivethru_avg_check'] = row['drivethru_gross'] / row['drivethru_transactions'] if row['drivethru_transactions'] > 0 else 0.0
        row['catering_avg_check'] = row['catering_gross'] / row['catering_transactions'] if row['catering_transactions'] > 0 else 0.0
        
        pivot_data[period] = row
    
    # Convert to list of DailySalesRow
    rows = [DailySalesRow(**row) for row in pivot_data.values()]
    
    # Sort by date ascending (beginning to end)
    rows.sort(key=lambda x: x.business_date, reverse=False)
    
    return DailySalesResponse(
        data=rows,
        total_rows=len(rows),
        date_range={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        filters={"brand_ids": brand_ids, "branch_ids": branch_ids}
    )


def export_daily_sales_to_excel(sales_response: DailySalesResponse) -> io.BytesIO:
    """
    Export DailySalesResponse to Excel format.
    
    Args:
        sales_response: DailySalesResponse object with pivot table data
    
    Returns:
        BytesIO buffer containing Excel file
    """
    # Convert sales data to list of dictionaries
    data_dicts = [row.model_dump() for row in sales_response.data]
    
    # Create DataFrame
    df = pd.DataFrame(data_dicts)
    
    # Reorder columns for better Excel layout
    column_order = [
        'business_date', 'period_label',
        # Total columns
        'total_gross', 'total_net', 'total_vat', 'total_discount', 
        'total_transactions', 'total_guests', 'total_avg_check',
        # Dinein columns
        'dinein_gross', 'dinein_net', 'dinein_vat', 'dinein_discount',
        'dinein_transactions', 'dinein_guests', 'dinein_avg_check', 'dinein_avg_by_guest',
        # Delivery columns
        'delivery_gross', 'delivery_net', 'delivery_vat', 'delivery_discount',
        'delivery_transactions', 'delivery_avg_check',
        # Takeaway columns
        'takeaway_gross', 'takeaway_net', 'takeaway_vat', 'takeaway_discount',
        'takeaway_transactions', 'takeaway_avg_check',
        # Drive Thru columns
        'drivethru_gross', 'drivethru_net', 'drivethru_vat', 'drivethru_discount',
        'drivethru_transactions', 'drivethru_avg_check',
        # Catering columns
        'catering_gross', 'catering_net', 'catering_vat', 'catering_discount',
        'catering_transactions', 'catering_avg_check',
    ]
    
    # Reorder (only include columns that exist in df)
    df = df[[col for col in column_order if col in df.columns]]
    
    # Rename columns for better readability in Excel
    df.columns = [
        'Date', 'Period',
        # Total
        'Total Gross', 'Total Net', 'Total VAT', 'Total Discount',
        'Total Trans', 'Total Guests', 'Total Avg Check',
        # Dinein
        'Dinein Gross', 'Dinein Net', 'Dinein VAT', 'Dinein Discount',
        'Dinein Trans', 'Dinein Guests', 'Dinein Avg Check', 'Dinein Avg/Guest',
        # Delivery
        'Delivery Gross', 'Delivery Net', 'Delivery VAT', 'Delivery Discount',
        'Delivery Trans', 'Delivery Avg Check',
        # Takeaway
        'Takeaway Gross', 'Takeaway Net', 'Takeaway VAT', 'Takeaway Discount',
        'Takeaway Trans', 'Takeaway Avg Check',
        # Drive Thru
        'Drive Thru Gross', 'Drive Thru Net', 'Drive Thru VAT', 'Drive Thru Discount',
        'Drive Thru Trans', 'Drive Thru Avg Check',
        # Catering
        'Catering Gross', 'Catering Net', 'Catering VAT', 'Catering Discount',
        'Catering Trans', 'Catering Avg Check',
    ]
    
    # Create Excel file in memory
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Daily Sales', index=False)
        
        # Get worksheet for formatting
        worksheet = writer.sheets['Daily Sales']
        
        # Auto-adjust column widths
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length, 50)
        
        # Format header row (bold)
        for cell in worksheet[1]:
            cell.font = cell.font.copy(bold=True)
    
    output.seek(0)
    return output
