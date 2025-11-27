#!/usr/bin/env python3
"""
Initialize V2 Budget Effect Calculation System
Creates the required database table and sets up the system
"""

import sqlite3
import os

# Database path
DB_PATH = "budget.db"

def initialize_v2_table():
    """Create the budget_effect_calculations_v2 table if it doesn't exist"""
    
    print("🔧 Initializing V2 Budget Effect Calculation System...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the V2 table with proper schema
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS budget_effect_calculations_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER NOT NULL,
        business_date TEXT NOT NULL,
        effect_type TEXT NOT NULL,
        effect_value REAL NOT NULL,
        metadata TEXT,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(branch_id, business_date, effect_type)
    )
    """
    
    print("📊 Creating budget_effect_calculations_v2 table...")
    cursor.execute(create_table_sql)
    
    # Create indexes for better query performance
    print("🔍 Creating indexes...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_v2_branch_date 
        ON budget_effect_calculations_v2(branch_id, business_date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_v2_effect_type 
        ON budget_effect_calculations_v2(effect_type)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_v2_business_date 
        ON budget_effect_calculations_v2(business_date)
    """)
    
    conn.commit()
    
    # Verify table creation
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_effect_calculations_v2'")
    result = cursor.fetchone()
    
    if result:
        print("✅ Table budget_effect_calculations_v2 created successfully")
        
        # Show table structure
        cursor.execute("PRAGMA table_info(budget_effect_calculations_v2)")
        columns = cursor.fetchall()
        print("\n📋 Table Structure:")
        for col in columns:
            print(f"   - {col[1]}: {col[2]}")
        
        # Check record count
        cursor.execute("SELECT COUNT(*) FROM budget_effect_calculations_v2")
        count = cursor.fetchone()[0]
        print(f"\n📊 Current records: {count}")
        
    else:
        print("❌ Failed to create table")
    
    conn.close()
    print("\n🎉 V2 System initialization complete!")

if __name__ == "__main__":
    initialize_v2_table()
