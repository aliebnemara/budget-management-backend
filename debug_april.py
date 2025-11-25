import pandas as pd
import pickle

# Load the data
with open('BaseData.pkl', 'rb') as f:
    df = pickle.load(f)

# Filter for Al Abraaj Bahrain Bay
branch_df = df[df['branch_name'] == 'Al Abraaj Bahrain Bay'].copy()

# Check April 2025 (CY) data
print("=" * 60)
print("APRIL 2025 (Compare Year) DATA:")
print("=" * 60)
april_2025 = branch_df[
    (branch_df['business_date'].dt.year == 2025) &
    (branch_df['business_date'].dt.month == 4)
].copy()

if len(april_2025) > 0:
    april_2025['day'] = april_2025['business_date'].dt.day
    print(f"\nTotal days in April 2025: {len(april_2025)}")
    print("\nFirst 10 days:")
    print(april_2025[['business_date', 'day', 'day_of_week', 'gross']].head(10).to_string(index=False))
    print(f"\nTotal April 2025 gross sales: {april_2025['gross'].sum():,.2f}")
    print(f"Average daily sales: {april_2025['gross'].mean():,.2f}")
    
    # Calculate weekday averages
    print("\nWeekday averages for all April 2025:")
    weekday_avg_all = april_2025.groupby('day_of_week')['gross'].mean()
    for dow, avg in weekday_avg_all.items():
        print(f"  {dow}: {avg:,.2f}")
    
    # Calculate weekday averages excluding first 3 days (Eid)
    april_2025_no_eid = april_2025[april_2025['day'] > 3]
    print(f"\nWeekday averages for April 2025 EXCLUDING first 3 days (Eid):")
    print(f"(Using days 4-30, total {len(april_2025_no_eid)} days)")
    weekday_avg_no_eid = april_2025_no_eid.groupby('day_of_week')['gross'].mean()
    for dow, avg in weekday_avg_no_eid.items():
        print(f"  {dow}: {avg:,.2f}")
    
    # Estimate what April 2026 should be (30 days, no Eid)
    # We need to know the day of week distribution for April 2026
    print("\n" + "=" * 60)
    print("APRIL 2026 ESTIMATION:")
    print("=" * 60)
    
    # Create April 2026 dates
    april_2026_dates = pd.date_range('2026-04-01', '2026-04-30', freq='D')
    april_2026_df = pd.DataFrame({'date': april_2026_dates})
    april_2026_df['day_of_week'] = april_2026_df['date'].dt.day_name()
    
    # Count weekdays in April 2026
    dow_counts = april_2026_df['day_of_week'].value_counts().sort_index()
    print("\nDay of week distribution in April 2026:")
    for dow, count in dow_counts.items():
        print(f"  {dow}: {count} days")
    
    # Calculate estimated total using April 2025 days 4-30 averages
    estimated_total = 0
    print("\nEstimated April 2026 sales using April 2025 (days 4-30) weekday averages:")
    for dow in dow_counts.index:
        if dow in weekday_avg_no_eid:
            count = dow_counts[dow]
            avg = weekday_avg_no_eid[dow]
            subtotal = count * avg
            estimated_total += subtotal
            print(f"  {dow}: {count} days × {avg:,.2f} = {subtotal:,.2f}")
    
    print(f"\n✅ EXPECTED APRIL 2026 TOTAL: {estimated_total:,.2f} BHD")
    print("   (This should match the tile value)")
    
else:
    print("❌ No April 2025 data found")

print("\n" + "=" * 60)
