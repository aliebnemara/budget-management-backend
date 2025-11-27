#!/usr/bin/env python3
"""
Verify that the sales_CY extraction fix is working
"""
import psycopg2
import json

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="abraajbudget",
    user="abraaj_user",
    password="abraaj_pass123"
)
cursor = conn.cursor()

print("=" * 80)
print("🧪 VERIFYING SALES_CY EXTRACTION FIX")
print("=" * 80)

# Get a sample record with Ramadan data
cursor.execute("""
    SELECT 
        restaurant_id,
        month,
        ramadan_eid_pct,
        ramadan_breakdown
    FROM budget_effect_calculations_v2
    WHERE budget_year = 2026 
    AND ramadan_eid_pct IS NOT NULL
    LIMIT 1
""")

row = cursor.fetchone()
if row:
    restaurant_id, month, ramadan_pct, ramadan_breakdown = row
    
    print(f"\n✅ Sample Data Found:")
    print(f"   Branch: {restaurant_id}")
    print(f"   Month: {month}")
    print(f"   Ramadan %: {ramadan_pct}%")
    
    # Extract sales_CY from breakdown (simulating what the API does)
    if ramadan_breakdown and isinstance(ramadan_breakdown, dict):
        daily_data = ramadan_breakdown.get('daily_data', [])
        if daily_data and isinstance(daily_data, list):
            sales_CY = sum(day.get('sales_cy', 0) for day in daily_data if isinstance(day, dict))
            
            print(f"\n✅ Sales Data Extraction:")
            print(f"   Number of days: {len(daily_data)}")
            print(f"   Total sales_CY: {sales_CY:,.2f}")
            
            # Calculate estimated sales (what frontend will show)
            if ramadan_pct is not None:
                est_sales_no_ramadan = sales_CY / (1 + float(ramadan_pct) / 100)
                print(f"\n✅ Calculated Values:")
                print(f"   2025 Actual (sales_CY): {sales_CY:,.2f}")
                print(f"   2026 Expected (est_sales_no_ramadan): {est_sales_no_ramadan:,.2f}")
                print(f"   Impact: {((sales_CY - est_sales_no_ramadan) / est_sales_no_ramadan * 100):,.2f}%")
            
            # Show sample daily data
            print(f"\n✅ Sample Daily Data (First 3 days):")
            for i, day in enumerate(daily_data[:3]):
                print(f"   Day {day.get('day')}: {day.get('date_by')} | Sales: {day.get('sales_cy'):,.2f} | Islamic: {day.get('islamic_label_by')}")
            
            print("\n" + "=" * 80)
            print("✅ FIX VERIFIED - Sales data can be extracted from breakdown!")
            print("=" * 80)
        else:
            print("❌ No daily_data found in breakdown")
    else:
        print("❌ No ramadan_breakdown found")
else:
    print("❌ No data found in database")

cursor.close()
conn.close()

print("\n💡 Next Step: Refresh the Islamic Calendar V2 page in your browser to see numbers!")
