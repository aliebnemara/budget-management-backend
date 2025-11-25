#!/usr/bin/env python3
"""
Test Smart Ramadan System with edge cases:
- Ramadan starting in December (spanning Dec-Jan)
- Ramadan starting in January (early year)
- Year boundary handling
"""

import sys
sys.path.insert(0, '/home/user/backend/Backend')

from src.services.smart_ramadan import SmartRamadanSystem
import pandas as pd

print("=" * 80)
print("🧪 TESTING SMART RAMADAN SYSTEM - EDGE CASES")
print("=" * 80)

# Test Case 1: Ramadan starts in December, ends in January
print("\n\n📌 TEST CASE 1: Ramadan Dec 2030 - Jan 2031")
print("─" * 80)
print("Scenario: Ramadan starts Dec 6, 2030 (spans Dec-Jan)")

config_dec_jan = {
    'compare_year': 2030,
    'ramadan_CY': '2030-12-06',  # Ramadan starts in December
    'ramadan_BY': '2031-11-25',  # Next year's Ramadan
    'ramadan_daycount_CY': 30,
    'ramadan_daycount_BY': 30
}

try:
    system_dec_jan = SmartRamadanSystem(config_dec_jan)
    affected = system_dec_jan.get_affected_months()
    
    print(f"\n✅ Month Detection: {affected}")
    print(f"   CY 2030: {affected['CY']}")  # Should include [12, 1]? No, 1 is 2031!
    print(f"   BY 2031: {affected['BY']}")
    
    # Test classification
    dec_15 = pd.Timestamp('2030-12-15')
    jan_5 = pd.Timestamp('2031-01-05')
    
    print(f"\n📅 Day Classification Tests:")
    print(f"   Dec 15, 2030: {system_dec_jan.classify_day(dec_15, 'CY')}")  # Should be 'ramadan'
    print(f"   Jan 5, 2031: {system_dec_jan.classify_day(jan_5, 'CY')}")   # Should be 'eid' or 'ramadan'
    
    # Generate estimation plan
    plan = system_dec_jan.generate_estimation_plan()
    print(f"\n✅ Estimation plan generated for {len(plan)} months")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()


# Test Case 2: Ramadan starts in January (early year)
print("\n\n📌 TEST CASE 2: Ramadan Jan 2032 - Feb 2032")
print("─" * 80)
print("Scenario: Ramadan starts Jan 15, 2032")

config_jan = {
    'compare_year': 2032,
    'ramadan_CY': '2032-01-15',  # Ramadan in January
    'ramadan_BY': '2033-01-04',  # Next year in January
    'ramadan_daycount_CY': 30,
    'ramadan_daycount_BY': 30
}

try:
    system_jan = SmartRamadanSystem(config_jan)
    affected_jan = system_jan.get_affected_months()
    
    print(f"\n✅ Month Detection: {affected_jan}")
    print(f"   CY 2032: {affected_jan['CY']}")  # Should include [1, 2]
    print(f"   BY 2033: {affected_jan['BY']}")
    
    # Test reference period selection for early months
    print(f"\n📅 Reference Period Selection Tests:")
    
    # Check what reference period is used for January BY days
    if 1 in system_jan.generate_estimation_plan():
        jan_plan = system_jan.generate_estimation_plan()[1]
        if 5 in jan_plan:
            ref = jan_plan[5]
            print(f"   Jan 5, 2033 reference: {ref['source_period']}")
    
    print(f"\n✅ Estimation plan generated successfully")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()


# Test Case 3: Check if month wraparound works
print("\n\n📌 TEST CASE 3: Month Wraparound in Reference Selection")
print("─" * 80)
print("Testing if system can find reference months when BY month is at year boundary")

config_boundary = {
    'compare_year': 2033,
    'ramadan_CY': '2033-12-15',  # Ramadan in December CY
    'ramadan_BY': '2034-01-10',  # Ramadan in January BY (needs Dec CY reference?)
    'ramadan_daycount_CY': 30,
    'ramadan_daycount_BY': 30
}

try:
    system_boundary = SmartRamadanSystem(config_boundary)
    affected_boundary = system_boundary.get_affected_months()
    
    print(f"\n✅ Month Detection: {affected_boundary}")
    print(f"   CY 2033: {affected_boundary['CY']}")
    print(f"   BY 2034: {affected_boundary['BY']}")
    
    # Generate plan to see if it handles boundary correctly
    plan_boundary = system_boundary.generate_estimation_plan()
    
    # Check if January 2034 normal days can find December reference
    if 1 in plan_boundary:
        # Look for a normal day in January after Ramadan/Eid
        for day_num in range(20, 32):  # Days likely after Ramadan/Eid
            if day_num in plan_boundary[1]:
                ref = plan_boundary[1][day_num]
                if ref['by_day_type'] == 'normal':
                    print(f"\n📅 Normal day {day_num} in Jan 2034:")
                    print(f"   Reference: {ref['source_period']}")
                    print(f"   Source months: {ref['source_months']}")
                    
                    # Check if December (month 12) is in source_months
                    if 12 in ref['source_months']:
                        print(f"   ✅ Successfully using December as reference!")
                    else:
                        print(f"   ⚠️  NOT using December (might be issue)")
                    break
    
    print(f"\n✅ Boundary test completed")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()


print("\n\n" + "=" * 80)
print("📋 EDGE CASE TEST SUMMARY")
print("=" * 80)
print("""
Key Questions Tested:
1. ✓ Can system detect Ramadan spanning December-January?
2. ✓ Can system handle Ramadan starting in January?
3. ? Can RULE 3 find December reference for January normal days?

Potential Issue Identified:
- Line 231 in smart_ramadan.py: test_month = by_month + (offset * direction)
- Does NOT wrap around year boundaries (1-12 constraint)
- May fail to find December reference for January normal days
""")
print("=" * 80)
