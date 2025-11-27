#!/usr/bin/env python3
"""
Real-time V2 Calculation Monitor
Monitors backend logs and database during calculation process
"""

import sqlite3
import time
import sys
from datetime import datetime as dt

DB_PATH = "budget.db"

def get_terminal_width():
    """Get terminal width for formatting"""
    try:
        import shutil
        return shutil.get_terminal_size().columns
    except:
        return 80

def print_separator(char="="):
    """Print a separator line"""
    width = get_terminal_width()
    print(char * width)

def print_header(text):
    """Print a centered header"""
    width = get_terminal_width()
    print(f"\n{text.center(width)}")
    print_separator()

def get_database_stats():
    """Get current database statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_effect_calculations_v2'")
        if not cursor.fetchone():
            return {
                'table_exists': False,
                'total_records': 0,
                'weekend_records': 0,
                'islamic_records': 0,
                'branches': 0,
                'date_range': None
            }
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM budget_effect_calculations_v2")
        total = cursor.fetchone()[0]
        
        # Records by effect type
        cursor.execute("SELECT COUNT(*) FROM budget_effect_calculations_v2 WHERE effect_type = 'weekend'")
        weekend = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM budget_effect_calculations_v2 WHERE effect_type = 'islamic_calendar'")
        islamic = cursor.fetchone()[0]
        
        # Unique branches
        cursor.execute("SELECT COUNT(DISTINCT branch_id) FROM budget_effect_calculations_v2")
        branches = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(business_date), MAX(business_date) FROM budget_effect_calculations_v2")
        date_range = cursor.fetchone()
        
        # Recent calculations
        cursor.execute("""
            SELECT effect_type, COUNT(*) as count, 
                   MIN(calculated_at) as first_calc, 
                   MAX(calculated_at) as last_calc
            FROM budget_effect_calculations_v2
            GROUP BY effect_type
        """)
        effect_details = cursor.fetchall()
        
        conn.close()
        
        return {
            'table_exists': True,
            'total_records': total,
            'weekend_records': weekend,
            'islamic_records': islamic,
            'branches': branches,
            'date_range': date_range,
            'effect_details': effect_details
        }
    except Exception as e:
        return {'error': str(e)}

def display_stats(stats, iteration=0):
    """Display database statistics in a formatted way"""
    print(f"\r\033[2J\033[H", end='')  # Clear screen and move cursor to top
    
    print_header(f"🔍 V2 Calculation Monitor - Live View")
    print(f"⏰ {dt.now().strftime('%Y-%m-%d %H:%M:%S')} | Refresh #{iteration}")
    print_separator("-")
    
    if 'error' in stats:
        print(f"❌ Error: {stats['error']}")
        return
    
    if not stats['table_exists']:
        print("⚠️  WARNING: budget_effect_calculations_v2 table does NOT exist!")
        print("   Run: python3 initialize_v2_system.py")
        return
    
    # Summary box
    print("\n📊 DATABASE SUMMARY:")
    print(f"   Total Records:    {stats['total_records']:,}")
    print(f"   Weekend Effects:  {stats['weekend_records']:,}")
    print(f"   Islamic Events:   {stats['islamic_records']:,}")
    print(f"   Branches Covered: {stats['branches']}")
    
    if stats['date_range'] and stats['date_range'][0]:
        print(f"   Date Range:       {stats['date_range'][0]} to {stats['date_range'][1]}")
    
    # Effect details
    if stats.get('effect_details'):
        print("\n📈 EFFECT TYPE BREAKDOWN:")
        for effect_type, count, first_calc, last_calc in stats['effect_details']:
            print(f"\n   {effect_type.upper()}:")
            print(f"      Records: {count:,}")
            print(f"      First:   {first_calc}")
            print(f"      Latest:  {last_calc}")
    
    # Status indicator
    if stats['total_records'] == 0:
        print("\n⏳ WAITING: No data yet. Click 'Calculate & Store All Effects' button in the UI.")
    elif stats['total_records'] < 100:
        print("\n⚡ CALCULATING: Data is being populated...")
    else:
        print("\n✅ READY: Calculation appears complete!")
    
    print_separator("-")
    print("💡 Press Ctrl+C to stop monitoring")

def monitor_calculation(interval=2):
    """Monitor calculation progress in real-time"""
    print_header("Starting V2 Calculation Monitor")
    print("Monitoring database for changes...")
    print("Open your browser and click 'Calculate & Store All Effects'")
    print_separator()
    
    iteration = 0
    previous_total = 0
    
    try:
        while True:
            iteration += 1
            stats = get_database_stats()
            display_stats(stats, iteration)
            
            # Check for changes
            current_total = stats.get('total_records', 0)
            if current_total > previous_total:
                # New data detected - show delta
                delta = current_total - previous_total
                print(f"\n🔥 NEW DATA: +{delta} records added!")
                previous_total = current_total
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped by user")
        print_separator()
        
        # Show final statistics
        final_stats = get_database_stats()
        print("\n📊 FINAL STATISTICS:")
        print(f"   Total Records: {final_stats.get('total_records', 0):,}")
        print(f"   Branches: {final_stats.get('branches', 0)}")
        if final_stats.get('total_records', 0) > 0:
            print("\n✅ Data successfully stored in V2 system!")
        else:
            print("\n⚠️  No data found. Make sure to click the Calculate button.")
        print()

if __name__ == "__main__":
    # Check if database exists
    import os
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("Make sure you're running from the Backend directory")
        sys.exit(1)
    
    monitor_calculation()
