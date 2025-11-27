#!/usr/bin/env python3
"""
Test the calculate endpoint manually to see what's happening
"""

import sys
sys.path.append('/home/user/backend/Backend')

from src.db.database import get_session
from src.services.effect_calculator_v2 import get_calculator_v2
from src.db.dbtables import BudgetEffectCalculationsV2

print("=" * 80)
print("MANUAL CALCULATION TEST")
print("=" * 80)

session = get_session()

# Get calculator
calculator = get_calculator_v2(session)

# Test with branch 233
test_branch_ids = [233]
test_budget_year = 2026
test_compare_year = 2025

islamic_dates = {
    'ramadan_CY': '2025-03-01',
    'ramadan_BY': '2026-02-18',
    'ramadan_daycount_CY': 30,
    'ramadan_daycount_BY': 30,
    'muharram_CY': '2025-07-06',
    'muharram_BY': '2026-06-26',
    'muharram_daycount_CY': 10,
    'muharram_daycount_BY': 10,
    'eid2_CY': '2025-06-07',
    'eid2_BY': '2026-05-27'
}

print(f"\nTest Parameters:")
print(f"  Branch IDs: {test_branch_ids}")
print(f"  Budget Year: {test_budget_year}")
print(f"  Compare Year: {test_compare_year}")
print(f"  Islamic Dates: {islamic_dates}")

print(f"\nCalling calculate_and_store_all_effects...")

try:
    results = calculator.calculate_and_store_all_effects(
        branch_ids=test_branch_ids,
        budget_year=test_budget_year,
        compare_year=test_compare_year,
        islamic_dates=islamic_dates,
        user_id=1
    )
    
    print(f"\n✅ Calculation completed!")
    print(f"   Results: {results}")
    
    # Check database
    count = session.query(BudgetEffectCalculationsV2).count()
    print(f"\n📊 Database records after calculation: {count}")
    
    if count > 0:
        # Show sample records
        samples = session.query(BudgetEffectCalculationsV2).limit(5).all()
        print(f"\nSample Records:")
        for record in samples:
            print(f"  Branch {record.restaurant_id}, Year {record.budget_year}, Month {record.month}")
            print(f"    Ramadan: {record.ramadan_eid_pct}, Muharram: {record.muharram_pct}, Eid2: {record.eid2_pct}")
    else:
        print("\n❌ No records in database after calculation!")
        print("   Check if:")
        print("   - Branch 233 exists in database")
        print("   - BaseData.pkl file exists and has data for this branch")
        print("   - Session commit is working")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    session.close()
