#!/usr/bin/env python3
"""
V2 Data Diagnostic Script
Comprehensive analysis of V2 calculation data
"""

import sqlite3
import json
from datetime import datetime as dt
from collections import defaultdict

DB_PATH = "budget.db"

def print_header(text, char="="):
    """Print formatted header"""
    print(f"\n{'=' * 80}")
    print(f"{text.center(80)}")
    print(f"{'=' * 80}\n")

def analyze_v2_data():
    """Perform comprehensive analysis of V2 data"""
    
    print_header("V2 DATA DIAGNOSTIC REPORT")
    print(f"Generated: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Table Structure
        print("1️⃣  TABLE STRUCTURE")
        print("-" * 80)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_effect_calculations_v2'")
        if not cursor.fetchone():
            print("❌ ERROR: budget_effect_calculations_v2 table does NOT exist!")
            print("   Solution: Run 'python3 initialize_v2_system.py'")
            conn.close()
            return
        
        cursor.execute("PRAGMA table_info(budget_effect_calculations_v2)")
        columns = cursor.fetchall()
        print("✅ Table exists with columns:")
        for col in columns:
            print(f"   {col[1]:20s} {col[2]:15s} {'NOT NULL' if col[3] else ''}")
        
        # 2. Record Counts
        print("\n2️⃣  RECORD COUNTS")
        print("-" * 80)
        
        cursor.execute("SELECT COUNT(*) FROM budget_effect_calculations_v2")
        total = cursor.fetchone()[0]
        print(f"Total Records: {total:,}")
        
        if total == 0:
            print("\n⚠️  NO DATA FOUND!")
            print("   Action Required: Click 'Calculate & Store All Effects' button")
            print("   Location: Budget Dashboard homepage")
            conn.close()
            return
        
        cursor.execute("""
            SELECT effect_type, COUNT(*) 
            FROM budget_effect_calculations_v2 
            GROUP BY effect_type
        """)
        effect_counts = cursor.fetchall()
        print("\nBy Effect Type:")
        for effect_type, count in effect_counts:
            percentage = (count / total * 100) if total > 0 else 0
            print(f"   {effect_type:20s} {count:>8,} ({percentage:>5.1f}%)")
        
        # 3. Branch Coverage
        print("\n3️⃣  BRANCH COVERAGE")
        print("-" * 80)
        
        cursor.execute("SELECT COUNT(DISTINCT branch_id) FROM budget_effect_calculations_v2")
        branch_count = cursor.fetchone()[0]
        print(f"Unique Branches: {branch_count}")
        
        cursor.execute("""
            SELECT branch_id, COUNT(*) as records
            FROM budget_effect_calculations_v2
            GROUP BY branch_id
            ORDER BY records DESC
            LIMIT 10
        """)
        top_branches = cursor.fetchall()
        print("\nTop 10 Branches by Record Count:")
        for branch_id, records in top_branches:
            print(f"   Branch {branch_id:>5}: {records:>6,} records")
        
        # 4. Date Range Analysis
        print("\n4️⃣  DATE RANGE ANALYSIS")
        print("-" * 80)
        
        cursor.execute("""
            SELECT MIN(business_date), MAX(business_date), COUNT(DISTINCT business_date)
            FROM budget_effect_calculations_v2
        """)
        min_date, max_date, unique_dates = cursor.fetchone()
        print(f"Date Range: {min_date} to {max_date}")
        print(f"Unique Dates: {unique_dates:,}")
        
        # Calculate expected date range
        from datetime import timedelta
        start = dt.strptime(min_date, '%Y-%m-%d')
        end = dt.strptime(max_date, '%Y-%m-%d')
        expected_days = (end - start).days + 1
        print(f"Expected Days: {expected_days}")
        if unique_dates < expected_days:
            print(f"⚠️  Missing {expected_days - unique_dates} days of data")
        else:
            print("✅ Complete date coverage")
        
        # 5. Islamic Calendar Events
        print("\n5️⃣  ISLAMIC CALENDAR EVENTS")
        print("-" * 80)
        
        cursor.execute("""
            SELECT business_date, branch_id, effect_value, metadata
            FROM budget_effect_calculations_v2
            WHERE effect_type = 'islamic_calendar' AND effect_value != 0
            ORDER BY business_date
            LIMIT 20
        """)
        islamic_events = cursor.fetchall()
        
        if islamic_events:
            print(f"Found {len(islamic_events)} sample Islamic calendar effects:")
            print(f"\n{'Date':<12} {'Branch':<8} {'Effect':<10} {'Event Details':<40}")
            print("-" * 80)
            for date, branch, effect, metadata in islamic_events[:10]:
                metadata_str = "No metadata"
                if metadata:
                    try:
                        meta_dict = json.loads(metadata)
                        if 'islamic_event' in meta_dict:
                            metadata_str = meta_dict['islamic_event']
                    except:
                        metadata_str = metadata[:40]
                print(f"{date:<12} {branch:<8} {effect:>9.2%} {metadata_str:<40}")
        else:
            print("⚠️  No Islamic calendar effects found (all values are 0)")
        
        # 6. Weekend Effects
        print("\n6️⃣  WEEKEND EFFECTS")
        print("-" * 80)
        
        cursor.execute("""
            SELECT business_date, branch_id, effect_value
            FROM budget_effect_calculations_v2
            WHERE effect_type = 'weekend' AND effect_value != 0
            ORDER BY ABS(effect_value) DESC
            LIMIT 10
        """)
        weekend_effects = cursor.fetchall()
        
        if weekend_effects:
            print("Top 10 Weekend Effects by Impact:")
            print(f"\n{'Date':<12} {'Branch':<8} {'Effect':<10}")
            print("-" * 80)
            for date, branch, effect in weekend_effects:
                print(f"{date:<12} {branch:<8} {effect:>9.2%}")
        else:
            print("⚠️  No significant weekend effects found")
        
        # 7. Calculation Timestamps
        print("\n7️⃣  CALCULATION TIMELINE")
        print("-" * 80)
        
        cursor.execute("""
            SELECT MIN(calculated_at), MAX(calculated_at)
            FROM budget_effect_calculations_v2
        """)
        first_calc, last_calc = cursor.fetchone()
        print(f"First Calculation: {first_calc}")
        print(f"Last Calculation:  {last_calc}")
        
        if first_calc and last_calc:
            first_time = dt.strptime(first_calc, '%Y-%m-%d %H:%M:%S')
            last_time = dt.strptime(last_calc, '%Y-%m-%d %H:%M:%S')
            duration = (last_time - first_time).total_seconds()
            print(f"Total Duration:    {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        # 8. Data Quality Checks
        print("\n8️⃣  DATA QUALITY CHECKS")
        print("-" * 80)
        
        # Check for NULL values
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN branch_id IS NULL THEN 1 ELSE 0 END) as null_branch,
                SUM(CASE WHEN business_date IS NULL THEN 1 ELSE 0 END) as null_date,
                SUM(CASE WHEN effect_type IS NULL THEN 1 ELSE 0 END) as null_type,
                SUM(CASE WHEN effect_value IS NULL THEN 1 ELSE 0 END) as null_value
            FROM budget_effect_calculations_v2
        """)
        null_checks = cursor.fetchone()
        
        issues = []
        if null_checks[0] > 0: issues.append(f"NULL branch_id: {null_checks[0]}")
        if null_checks[1] > 0: issues.append(f"NULL business_date: {null_checks[1]}")
        if null_checks[2] > 0: issues.append(f"NULL effect_type: {null_checks[2]}")
        if null_checks[3] > 0: issues.append(f"NULL effect_value: {null_checks[3]}")
        
        if issues:
            print("⚠️  Data Quality Issues Found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ No NULL values found - data integrity good")
        
        # Check for duplicates
        cursor.execute("""
            SELECT branch_id, business_date, effect_type, COUNT(*) as cnt
            FROM budget_effect_calculations_v2
            GROUP BY branch_id, business_date, effect_type
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"\n⚠️  Found {len(duplicates)} duplicate records:")
            for branch, date, etype, cnt in duplicates[:5]:
                print(f"   Branch {branch}, {date}, {etype}: {cnt} copies")
        else:
            print("✅ No duplicate records found")
        
        # 9. Summary & Recommendations
        print("\n9️⃣  SUMMARY & RECOMMENDATIONS")
        print("-" * 80)
        
        if total > 0:
            print("✅ V2 system is operational and contains data")
            print(f"✅ {total:,} effect calculations stored")
            print(f"✅ {branch_count} branches covered")
            print(f"✅ {unique_dates:,} unique dates")
            
            if len(effect_counts) >= 2:
                print("✅ Both weekend and Islamic calendar effects calculated")
            else:
                print("⚠️  Only one effect type found - check calculation")
            
            print("\n📊 Next Steps:")
            print("   1. View results in 'Weekend Effect V2' page")
            print("   2. View results in 'Islamic Calendar V2' page")
            print("   3. Compare with V1 results for validation")
        else:
            print("❌ No data found in V2 system")
            print("\n📋 Action Required:")
            print("   1. Open Budget Dashboard")
            print("   2. Click 'Calculate & Store All Effects' button")
            print("   3. Wait for calculation to complete")
            print("   4. Run this diagnostic script again")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_v2_data()
    print("\n" + "=" * 80)
    print("Diagnostic complete!".center(80))
    print("=" * 80 + "\n")
