#!/usr/bin/env python3
"""
Critical Test: Can January normal days use December as reference?

Scenario:
- Ramadan CY: March-April (doesn't affect Jan or Dec)
- Ramadan BY: January (affects only January)
- Question: Can January BY normal days use December CY as reference?
"""

import sys
sys.path.insert(0, '/home/user/backend/Backend')

from src.services.smart_ramadan import SmartRamadanSystem

print("=" * 80)
print("🔍 CRITICAL TEST: January Normal Days → December Reference")
print("=" * 80)

config = {
    'compare_year': 2025,
    'ramadan_CY': '2025-03-01',      # March-April (not affecting Jan/Dec)
    'ramadan_BY': '2026-01-15',      # January only
    'ramadan_daycount_CY': 30,
    'ramadan_daycount_BY': 15  # Short Ramadan, only half of January
}

print("\n📅 Configuration:")
print(f"   CY Ramadan: March-April 2025 (Jan/Dec are NORMAL)")
print(f"   BY Ramadan: Jan 15-29, 2026 (Jan 1-14 and Jan 30-31 are NORMAL)")
print(f"\n🎯 Question: Can Jan 1-14 and Jan 30-31 (normal days) use Dec 2025 as reference?")

system = SmartRamadanSystem(config)
affected = system.get_affected_months()

print(f"\n✅ Affected Months:")
print(f"   CY 2025: {affected['CY']}")  # Should be [3, 4]
print(f"   BY 2026: {affected['BY']}")  # Should be [1, 2] (Ramadan + Eid)

# Generate plan
plan = system.generate_estimation_plan()

# Check January normal days
if 1 in plan:
    print(f"\n📅 Checking January 2026 Normal Days:")
    
    # Day 5 (before Ramadan - should be normal)
    if 5 in plan[1]:
        ref = plan[1][5]
        print(f"\n   Day 5 (Jan 5, 2026):")
        print(f"   - Type: {ref['by_day_type']}")
        print(f"   - Reference: {ref['source_period']}")
        print(f"   - Source months: {ref['source_months']}")
        
        if ref['by_day_type'] == 'normal':
            if 12 in ref['source_months']:
                print(f"   ✅ SUCCESS: Using December as reference!")
            elif 1 in ref['source_months']:
                print(f"   ⚠️  ISSUE: Using January CY (but Jan CY is also normal, so OK)")
            else:
                print(f"   ❌ PROBLEM: Not using nearby month (Dec or Jan)")
    
    # Day 30 (after Ramadan/Eid - should be normal)
    if 30 in plan[1]:
        ref = plan[1][30]
        print(f"\n   Day 30 (Jan 30, 2026):")
        print(f"   - Type: {ref['by_day_type']}")
        print(f"   - Reference: {ref['source_period']}")
        print(f"   - Source months: {ref['source_months']}")
        
        if ref['by_day_type'] == 'normal':
            if 12 in ref['source_months']:
                print(f"   ✅ SUCCESS: Using December as reference!")
            elif 1 in ref['source_months']:
                print(f"   ✅ ACCEPTABLE: Using January CY (normal days)")
            else:
                print(f"   ❌ PROBLEM: Not using nearby month")

# Now test the opposite: Can December BY use January CY?
print("\n\n" + "=" * 80)
print("🔍 REVERSE TEST: December Normal Days → January Reference")
print("=" * 80)

config2 = {
    'compare_year': 2028,
    'ramadan_CY': '2028-03-01',      # March-April (not affecting Jan/Dec)
    'ramadan_BY': '2029-12-15',      # December only
    'ramadan_daycount_CY': 30,
    'ramadan_daycount_BY': 15  # Short Ramadan
}

print("\n📅 Configuration:")
print(f"   CY Ramadan: March-April 2028 (Jan/Dec are NORMAL)")
print(f"   BY Ramadan: Dec 15-29, 2029")
print(f"\n🎯 Question: Can Dec 1-14 (normal days) use Jan 2029 as reference?")

system2 = SmartRamadanSystem(config2)
plan2 = system2.generate_estimation_plan()

if 12 in plan2:
    print(f"\n📅 Checking December 2029 Normal Days:")
    
    if 5 in plan2[12]:
        ref = plan2[12][5]
        print(f"\n   Day 5 (Dec 5, 2029):")
        print(f"   - Type: {ref['by_day_type']}")
        print(f"   - Reference: {ref['source_period']}")
        print(f"   - Source months: {ref['source_months']}")
        
        if ref['by_day_type'] == 'normal':
            if 1 in ref['source_months']:
                print(f"   ⚠️  ISSUE: Using January CY (wraps forward, but works)")
            elif 12 in ref['source_months']:
                print(f"   ✅ SUCCESS: Using December CY (same month)")
            else:
                print(f"   Using month {ref['source_months'][0]}")

print("\n" + "=" * 80)
print("📋 CONCLUSION")
print("=" * 80)
print("""
The current logic (line 231):
    test_month = by_month + (offset * direction)
    if 1 <= test_month <= 12 and test_month not in cy_affected_months:

✅ Works within year boundaries (months 2-11)
⚠️  Limited at year boundaries:
   - January (month 1) cannot look back to December (month 12)
   - December (month 12) cannot look forward to January (month 1)
   
✅ MITIGATION: Fallback logic (lines 238-243) finds ANY unaffected month
   - Not optimal, but ensures system never fails
   - May use distant month instead of adjacent month across year boundary

🎯 RECOMMENDATION: Add modulo arithmetic for true wraparound:
   test_month = ((by_month - 1) + (offset * direction)) % 12 + 1
""")
print("=" * 80)
