import pandas as pd
import pickle
import sys
from datetime import datetime, timedelta

print("=" * 80)
print("COMPREHENSIVE APRIL 2026 CALCULATION DEBUG")
print("=" * 80)

# Load data
with open('BaseData.pkl', 'rb') as f:
    df = pickle.load(f)

print(f"\nTotal records in BaseData: {len(df):,}")
print(f"Columns: {df.columns.tolist()}")

# Parameters from user's request
compare_year = 2025
budget_year = 2026
ramadan_start_CY = datetime(2025, 3, 1)
ramadan_days_CY = 30
ramadan_start_BY = datetime(2026, 2, 18)
ramadan_days_BY = 30

ramadan_end_CY = ramadan_start_CY + timedelta(days=ramadan_days_CY - 1)
eid_start_CY = ramadan_end_CY + timedelta(days=1)
eid_end_CY = eid_start_CY + timedelta(days=3)

print(f"\nRamadan CY 2025: {ramadan_start_CY.strftime('%Y-%m-%d')} to {ramadan_end_CY.strftime('%Y-%m-%d')}")
print(f"Eid CY 2025: {eid_start_CY.strftime('%Y-%m-%d')} to {eid_end_CY.strftime('%Y-%m-%d')}")
print(f"  → March 1-30 = Ramadan")
print(f"  → March 31 = Eid day 1")
print(f"  → April 1-3 = Eid days 2-4")

# Check what branches exist
print(f"\n{'=' * 80}")
print("BRANCH ANALYSIS")
print("=" * 80)
branches = df['branch_id'].unique()
print(f"Total branches: {len(branches)}")
print(f"Branch IDs sample: {sorted(branches)[:10]}")

# For debugging, let's use the first available branch
test_branch = branches[0]
print(f"\n🎯 Using branch_id: {test_branch} for testing")

branch_df = df[df['branch_id'] == test_branch].copy()
print(f"Records for this branch: {len(branch_df):,}")

# Check April 2025 data
print(f"\n{'=' * 80}")
print("APRIL 2025 (CY) DATA ANALYSIS")
print("=" * 80)

april_2025 = branch_df[
    (branch_df['business_date'].dt.year == 2025) &
    (branch_df['business_date'].dt.month == 4)
].copy()

if len(april_2025) > 0:
    april_2025 = april_2025.sort_values('business_date')
    print(f"\nTotal days in April 2025: {len(april_2025)}")
    print(f"Total sales: {april_2025['gross'].sum():,.2f} BHD")
    print(f"Average per day: {april_2025['gross'].mean():,.2f} BHD")
    
    print(f"\nFirst 10 days of April 2025:")
    print(april_2025[['business_date', 'day_of_week', 'gross']].head(10).to_string(index=False))
    
    # Weekday averages for ALL April 2025
    print(f"\n📊 Weekday Averages - ALL April 2025 (30 days):")
    weekday_avg_all = april_2025.groupby('day_of_week')['gross'].agg(['mean', 'count'])
    for dow, row in weekday_avg_all.iterrows():
        print(f"  {dow:9s}: {row['mean']:8,.2f} BHD (n={int(row['count'])} days)")
    
    # Weekday averages EXCLUDING first 3 days (Eid)
    april_2025['day'] = april_2025['business_date'].dt.day
    april_2025_no_eid = april_2025[april_2025['day'] > 3]
    
    print(f"\n📊 Weekday Averages - April 2025 EXCLUDING first 3 days (Eid):")
    print(f"   Using days 4-30 ({len(april_2025_no_eid)} days total)")
    weekday_avg_no_eid = april_2025_no_eid.groupby('day_of_week')['gross'].agg(['mean', 'count'])
    for dow, row in weekday_avg_no_eid.iterrows():
        print(f"  {dow:9s}: {row['mean']:8,.2f} BHD (n={int(row['count'])} days)")
    
    # Expected April 2026 calculation
    print(f"\n{'=' * 80}")
    print("APRIL 2026 (BY) EXPECTED CALCULATION")
    print("=" * 80)
    
    # Create April 2026 calendar
    april_2026_dates = pd.date_range('2026-04-01', '2026-04-30', freq='D')
    april_2026_cal = pd.DataFrame({
        'date': april_2026_dates,
        'day_of_week': april_2026_dates.strftime('%A')
    })
    
    print(f"\nApril 2026 has 30 days")
    print(f"\nDay of week distribution in April 2026:")
    dow_counts = april_2026_cal['day_of_week'].value_counts().sort_index()
    for dow, count in dow_counts.items():
        print(f"  {dow:9s}: {count} days")
    
    # Calculate expected using days 4-30 averages
    print(f"\n💰 EXPECTED APRIL 2026 SALES (using April 2025 days 4-30 averages):")
    total_expected = 0
    for dow in dow_counts.index:
        if dow in weekday_avg_no_eid.index:
            count = dow_counts[dow]
            avg = weekday_avg_no_eid.loc[dow, 'mean']
            subtotal = count * avg
            total_expected += subtotal
            print(f"  {dow:9s}: {count} × {avg:8,.2f} = {subtotal:10,.2f} BHD")
    
    print(f"\n✅ EXPECTED APRIL 2026 TOTAL: {total_expected:,.2f} BHD")
    print(f"   This should match both:")
    print(f"   - Table total in daily breakdown")
    print(f"   - 'Expected Sales' tile for April 2026")
    
else:
    print("❌ No April 2025 data found for this branch!")

# Now check what the service layer is actually doing
print(f"\n{'=' * 80}")
print("SERVICE LAYER SIMULATION")
print("=" * 80)

# Try to replicate what Ramadan_Eid_Calculations does
print("\nTrying to understand ramadan_CY and ramadan_BY flag values...")

# Check if these columns exist in the data
if 'ramadan_CY' in df.columns:
    print(f"✅ ramadan_CY column exists")
    print(f"   Unique values: {sorted(df['ramadan_CY'].dropna().unique())}")
else:
    print(f"❌ ramadan_CY column does NOT exist in BaseData.pkl")
    print(f"   This means flags are calculated on-the-fly in the service layer")

if 'ramadan_BY' in df.columns:
    print(f"✅ ramadan_BY column exists")
    print(f"   Unique values: {sorted(df['ramadan_BY'].dropna().unique())}")
else:
    print(f"❌ ramadan_BY column does NOT exist in BaseData.pkl")
    print(f"   This means flags are calculated on-the-fly in the service layer")

print(f"\n{'=' * 80}")
print("RECOMMENDATIONS")
print("=" * 80)
print("""
The service layer (Ramadan_Eid_Calculations function) needs to:

1. Calculate ramadan_CY flags for April 2025:
   - Days 1-3: ramadan_CY = 2 (Eid)
   - Days 4-30: ramadan_CY = 0 (Normal)

2. Calculate weekday averages from April 2025 days 4-30 ONLY

3. Apply these averages to ALL 30 days of April 2026

4. The result should be approximately {total_expected:,.2f} BHD

If the table is showing 53,905 BHD instead of 57,295 BHD:
- Check what reference period is actually being used
- Check if all 30 days of April 2026 are getting values
- Check if wrong weekday averages are being applied
""")

print("\n" + "=" * 80)
