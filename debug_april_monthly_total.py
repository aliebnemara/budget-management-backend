import pandas as pd
import pickle
from datetime import datetime, timedelta

print("=" * 80)
print("APRIL 2026 MONTHLY TOTAL CALCULATION - Branch 189")
print("=" * 80)

# Load data
with open('BaseData.pkl', 'rb') as f:
    df = pickle.load(f)

# Filter for branch 189 (Al Abraaj Sehla)
branch_189 = df[df['branch_id'] == 189].copy()
print(f"\nBranch 189 total records: {len(branch_189):,}")

# STEP 1: Aggregate to DAILY totals (sum all transactions per day)
print(f"\n{'=' * 80}")
print("STEP 1: AGGREGATE TO DAILY TOTALS")
print("=" * 80)

daily_totals = branch_189.groupby(['business_date', 'day_of_week'])['gross'].sum().reset_index()
print(f"Total unique days: {len(daily_totals):,}")

# STEP 2: Get April 2025 daily totals
print(f"\n{'=' * 80}")
print("STEP 2: APRIL 2025 DAILY TOTALS")
print("=" * 80)

april_2025_daily = daily_totals[
    (daily_totals['business_date'].dt.year == 2025) &
    (daily_totals['business_date'].dt.month == 4)
].copy()

april_2025_daily['day'] = april_2025_daily['business_date'].dt.day
april_2025_daily = april_2025_daily.sort_values('business_date')

print(f"\nApril 2025: {len(april_2025_daily)} days")
print(f"Total April 2025 sales: {april_2025_daily['gross'].sum():,.2f} BHD")
print(f"\nFirst 10 days:")
print(april_2025_daily[['business_date', 'day_of_week', 'day', 'gross']].head(10).to_string(index=False))

# STEP 3: Calculate weekday averages for ALL April 2025
print(f"\n{'=' * 80}")
print("STEP 3: WEEKDAY AVERAGES - ALL APRIL 2025")
print("=" * 80)

weekday_avg_all = april_2025_daily.groupby('day_of_week')['gross'].agg(['mean', 'sum', 'count'])
print("\nAll 30 days of April 2025:")
for dow, row in weekday_avg_all.iterrows():
    print(f"  {dow:9s}: {row['count']:2.0f} days, Total={row['sum']:8,.2f}, Avg={row['mean']:8,.2f} BHD")

# STEP 4: Calculate weekday averages EXCLUDING first 3 days (Eid)
print(f"\n{'=' * 80}")
print("STEP 4: WEEKDAY AVERAGES - APRIL 2025 EXCLUDING FIRST 3 DAYS (EID)")
print("=" * 80)

april_2025_no_eid = april_2025_daily[april_2025_daily['day'] > 3]
print(f"\nUsing days 4-30 ({len(april_2025_no_eid)} days)")
print(f"Total sales (days 4-30): {april_2025_no_eid['gross'].sum():,.2f} BHD")

weekday_avg_no_eid = april_2025_no_eid.groupby('day_of_week')['gross'].agg(['mean', 'sum', 'count'])
print("\nWeekday averages (excluding Eid days 1-3):")
for dow, row in weekday_avg_no_eid.iterrows():
    print(f"  {dow:9s}: {row['count']:2.0f} days, Total={row['sum']:8,.2f}, Avg={row['mean']:8,.2f} BHD")

# STEP 5: Calculate expected April 2026 MONTHLY TOTAL
print(f"\n{'=' * 80}")
print("STEP 5: EXPECTED APRIL 2026 MONTHLY TOTAL")
print("=" * 80)

# April 2026 day of week distribution
april_2026_dates = pd.date_range('2026-04-01', '2026-04-30', freq='D')
april_2026_dow = pd.Series([d.strftime('%A') for d in april_2026_dates])
dow_counts_2026 = april_2026_dow.value_counts().sort_index()

print("\nApril 2026 day distribution:")
for dow, count in dow_counts_2026.items():
    print(f"  {dow:9s}: {count} days")

print("\n💰 EXPECTED APRIL 2026 CALCULATION:")
print("   (Using April 2025 days 4-30 weekday averages)")
print()

total_expected = 0
for dow in dow_counts_2026.index:
    if dow in weekday_avg_no_eid.index:
        count = dow_counts_2026[dow]
        avg = weekday_avg_no_eid.loc[dow, 'mean']
        subtotal = count * avg
        total_expected += subtotal
        print(f"  {dow:9s}: {count} days × {avg:8,.2f} = {subtotal:10,.2f} BHD")
    else:
        print(f"  {dow:9s}: No data available!")

print(f"\n" + "=" * 80)
print(f"✅ EXPECTED APRIL 2026 MONTHLY TOTAL: {total_expected:,.2f} BHD")
print("=" * 80)
print("\nThis should match:")
print("  1. The 'Expected Sales' tile for April 2026")
print("  2. The SUM of all daily estimated values in the table")
print()

# STEP 6: Compare with what service layer should return
print(f"\n{'=' * 80}")
print("STEP 6: WHAT TO VERIFY")
print("=" * 80)
print(f"""
In the frontend:

1. April 2026 'Expected Sales' tile should show: {total_expected:,.2f} BHD

2. The daily breakdown table should show:
   - 30 rows (one per day)
   - Each day has an estimated value based on weekday average
   - SUM of all estimated values = {total_expected:,.2f} BHD

3. If the tile shows 0 or wrong value:
   - Service layer (Ramadan_Eid_Calculations) is not calculating correctly
   - Check if gross_BY values are being set for April 2026
   - Check if sum_sales is including April in the aggregation

4. If the table shows wrong total (like 53,905):
   - Check what reference period is being used
   - Check if all 30 days are getting estimated values
   - Check if correct weekday averages are applied
""")
