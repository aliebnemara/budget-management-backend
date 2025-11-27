"""
Database Migration Script: Add Budget Effect Calculations V2 Table
===================================================================

This script creates the budget_effect_calculations_v2 table for storing
pre-calculated weekend and Islamic calendar effects. This enables the
"Calculate Once, View Many Times" pattern for 10-20x faster page loads.

Table Structure:
- restaurant_id, budget_year, month: Unique constraint
- weekday_effect_pct, ramadan_eid_pct, muharram_pct, eid2_pct: Final percentages
- weekday_breakdown, ramadan_breakdown, muharram_breakdown, eid2_breakdown: JSONB detailed data
- calculated_at, calculated_by: Audit metadata

Usage:
    python migrations/add_budget_effect_calculations_v2.py
    
Requirements:
    - Database connection configured in .env file
    - PostgreSQL database with JSONB support
    - User must have CREATE TABLE permissions
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the database migration to create budget_effect_calculations_v2 table"""
    
    db_url = os.getenv('DB_Link')
    if not db_url:
        print("❌ Error: DB_Link not found in environment variables")
        return False
    
    print("=" * 80)
    print("🔄 Starting Database Migration: Create budget_effect_calculations_v2 Table")
    print("=" * 80)
    print(f"📅 Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Database: {db_url.split('@')[1] if '@' in db_url else 'Unknown'}")
    print()
    
    try:
        # Create database engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            print("✅ Database connection established")
            print()
            
            # Start transaction
            trans = conn.begin()
            
            try:
                # ==============================================================
                # CREATE BUDGET_EFFECT_CALCULATIONS_V2 TABLE
                # ==============================================================
                print("📊 Creating budget_effect_calculations_v2 table...")
                print("-" * 80)
                
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS budget_effect_calculations_v2 (
                    id SERIAL PRIMARY KEY,
                    restaurant_id INTEGER NOT NULL REFERENCES branch(id),
                    budget_year INTEGER NOT NULL,
                    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
                    
                    -- Final effect percentages
                    weekday_effect_pct NUMERIC(10, 4),
                    ramadan_eid_pct NUMERIC(10, 4),
                    muharram_pct NUMERIC(10, 4),
                    eid2_pct NUMERIC(10, 4),
                    
                    -- Detailed breakdowns as JSONB
                    weekday_breakdown JSONB,
                    ramadan_breakdown JSONB,
                    muharram_breakdown JSONB,
                    eid2_breakdown JSONB,
                    
                    -- Audit metadata
                    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    calculated_by INTEGER REFERENCES users(id),
                    
                    -- Unique constraint: one record per restaurant/year/month
                    CONSTRAINT uq_budget_effect_calc_v2_rest_year_month 
                        UNIQUE (restaurant_id, budget_year, month)
                )
                """
                
                conn.execute(text(create_table_sql))
                print("   ✅ Table budget_effect_calculations_v2 created successfully")
                
                # ==============================================================
                # CREATE INDEXES FOR PERFORMANCE
                # ==============================================================
                print()
                print("📊 Creating indexes for optimal query performance...")
                print("-" * 80)
                
                indexes = [
                    {
                        "name": "idx_budget_effect_v2_rest_year",
                        "sql": """
                        CREATE INDEX IF NOT EXISTS idx_budget_effect_v2_rest_year 
                        ON budget_effect_calculations_v2 (restaurant_id, budget_year)
                        """
                    },
                    {
                        "name": "idx_budget_effect_v2_restaurant",
                        "sql": """
                        CREATE INDEX IF NOT EXISTS idx_budget_effect_v2_restaurant 
                        ON budget_effect_calculations_v2 (restaurant_id)
                        """
                    },
                    {
                        "name": "idx_budget_effect_v2_year",
                        "sql": """
                        CREATE INDEX IF NOT EXISTS idx_budget_effect_v2_year 
                        ON budget_effect_calculations_v2 (budget_year)
                        """
                    }
                ]
                
                for idx in indexes:
                    conn.execute(text(idx["sql"]))
                    print(f"   ✅ Index {idx['name']} created successfully")
                
                # Commit transaction
                trans.commit()
                
                print()
                print("=" * 80)
                print("✅ Migration completed successfully!")
                print("=" * 80)
                print()
                print("📋 Summary:")
                print("   ✅ Table 'budget_effect_calculations_v2' created")
                print("   ✅ 3 indexes created for optimal performance")
                print("   ✅ Unique constraint on (restaurant_id, budget_year, month)")
                print("   ✅ Foreign keys to branch and users tables")
                print()
                print("🚀 Next Steps:")
                print("   1. Create EffectCalculatorV2 service")
                print("   2. Build API endpoints for calculate & retrieve")
                print("   3. Create V2 frontend pages")
                print()
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during migration: {str(e)}")
                print("   Transaction rolled back")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False

if __name__ == "__main__":
    print()
    success = run_migration()
    print()
    
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
