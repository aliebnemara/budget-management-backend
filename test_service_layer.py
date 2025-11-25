import pandas as pd
import pickle
from datetime import datetime
from src.services.budget import Ramadan_Eid_Calculations

print("=" * 80)
print("TESTING SERVICE LAYER DIRECTLY")
print("=" * 80)

# Load data
with open('BaseData.pkl', 'rb') as f:
    df = pickle.load(f)

# Parameters
compare_year = 2025
ramadan_CY = datetime(2025, 3, 1)
ramadan_BY = datetime(2026, 2, 18)
ramadan_daycount_CY = 30
ramadan_daycount_BY = 30

print(f"\nCalling Ramadan_Eid_Calculations...")
print(f"  compare_year: {compare_year}")
print(f"  ramadan_CY: {ramadan_CY}")
print(f"  ramadan_BY: {ramadan_BY}")

# Call the service function
result = Ramadan_Eid_Calculations(
    compare_year=compare_year,
    ramadan_CY=ramadan_CY,
    ramadan_BY=ramadan_BY,
    ramadan_daycount_CY=ramadan_daycount_CY,
    ramadan_daycount_BY=ramadan_daycount_BY,
    df=df
)

print(f"\n✅ Function returned successfully")
print(f"Result type: {type(result)}")
print(f"Result shape: {result.shape if hasattr(result, 'shape') else 'N/A'}")
print(f"\nResult columns: {result.columns.tolist() if hasattr(result, 'columns') else 'N/A'}")

# Filter for branch 189, April
branch_189_april = result[
    (result['branch_id'] == 189) &
    (result['month'] == 4)
]

if len(branch_189_april) > 0:
    print(f"\n{'=' * 80}")
    print("BRANCH 189 - APRIL 2026 RESULTS")
    print("=" * 80)
    print(branch_189_april.to_string(index=False))
    
    est_value = branch_189_april['est'].values[0]
    actual_value = branch_189_april['actual'].values[0]
    
    print(f"\n🔍 KEY VALUES:")
    print(f"   Actual (April 2026): {actual_value:,.2f} BHD")
    print(f"   Estimated (no Ramadan): {est_value:,.2f} BHD")
    print(f"\n   Expected: 57,298.93 BHD")
    print(f"   Match: {'✅ CORRECT!' if abs(est_value - 57298.93) < 100 else '❌ WRONG!'}")
else:
    print(f"\n❌ No April data found for branch 189")
    print(f"\nAll branch 189 data:")
    print(result[result['branch_id'] == 189].to_string(index=False))
