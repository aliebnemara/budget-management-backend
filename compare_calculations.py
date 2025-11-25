import pandas as pd
import pickle
from datetime import datetime

print("=" * 80)
print("COMPARING SERVICE LAYER vs SMART SYSTEM CALCULATIONS")
print("=" * 80)

# Load data
with open('BaseData.pkl', 'rb') as f:
    df = pickle.load(f)

# Filter for branch 189
branch_189 = df[df['branch_id'] == 189].copy()

# Aggregate to daily totals (same as service layer does)
daily_totals = branch_189.groupby(['business_date', 'day_of_week'])['gross'].sum().reset_index()

# Get April 2025 data
april_2025 = daily_totals[
    (daily_totals['business_date'].dt.year == 2025) &
    (daily_totals['business_date'].dt.month == 4)
].copy()

april_2025['day'] = april_2025['business_date'].dt.day

print(f"\n{'=' * 80}")
print("METHOD 1: SERVICE LAYER (excludes days 1-3)")
print("=" * 80)

# Exclude days 1-3 (what service layer should do)
april_2025_service = april_2025[april_2025['day'] > 3].copy()
print(f"Days used: 4-30 ({len(april_2025_service)} days)")
print(f"Total: {april_2025_service['gross'].sum():,.2f}")

weekday_avg_service = april_2025_service.groupby('day_of_week')['gross'].mean()
print("\nWeekday averages (service layer):")
for dow, avg in weekday_avg_service.items():
    print(f"  {dow:9s}: {avg:8,.2f}")

# Calculate April 2026 using service layer averages
april_2026_dates = pd.date_range('2026-04-01', '2026-04-30', freq='D')
dow_counts = pd.Series([d.strftime('%A') for d in april_2026_dates]).value_counts()

total_service = sum(dow_counts[dow] * weekday_avg_service[dow] for dow in dow_counts.index if dow in weekday_avg_service.index)
print(f"\n✅ SERVICE LAYER TOTAL: {total_service:,.2f} BHD")

print(f"\n{'=' * 80}")
print("METHOD 2: SMART SYSTEM (uses date range filter)")
print("=" * 80)

# Smart system uses date range: April 4-30, 2025
april_start = datetime(2025, 4, 4)
april_end = datetime(2025, 4, 30)

# Get all transactions within date range (NOT daily aggregated yet)
april_2025_smart_raw = branch_189[
    (branch_189['business_date'] >= april_start) &
    (branch_189['business_date'] <= april_end)
].copy()

print(f"Transactions in range: {len(april_2025_smart_raw):,}")
print(f"Total gross: {april_2025_smart_raw['gross'].sum():,.2f}")

# Smart system aggregates to daily first, then calculates averages
april_2025_smart_raw['day_of_week'] = april_2025_smart_raw['business_date'].dt.day_name()
daily_totals_smart = april_2025_smart_raw.groupby(['business_date', 'day_of_week'])['gross'].sum().reset_index()

print(f"Unique days after aggregation: {len(daily_totals_smart)}")

weekday_avg_smart = daily_totals_smart.groupby('day_of_week')['gross'].mean()
print("\nWeekday averages (smart system):")
for dow, avg in weekday_avg_smart.items():
    print(f"  {dow:9s}: {avg:8,.2f}")

total_smart = sum(dow_counts[dow] * weekday_avg_smart[dow] for dow in dow_counts.index if dow in weekday_avg_smart.index)
print(f"\n✅ SMART SYSTEM TOTAL: {total_smart:,.2f} BHD")

print(f"\n{'=' * 80}")
print("COMPARISON")
print("=" * 80)
print(f"Service layer:  {total_service:,.2f} BHD")
print(f"Smart system:   {total_smart:,.2f} BHD")
print(f"Difference:     {abs(total_service - total_smart):,.2f} BHD")
print()

if abs(total_service - total_smart) < 0.01:
    print("✅ PERFECT MATCH!")
else:
    print("❌ DISCREPANCY FOUND!")
    print("\nChecking for differences in weekday averages:")
    for dow in weekday_avg_service.index:
        if dow in weekday_avg_smart.index:
            diff = weekday_avg_service[dow] - weekday_avg_smart[dow]
            if abs(diff) > 0.01:
                print(f"  {dow}: Service={weekday_avg_service[dow]:,.2f}, Smart={weekday_avg_smart[dow]:,.2f}, Diff={diff:,.2f}")
