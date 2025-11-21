#!/usr/bin/env python3
"""
Initialize BudgetRuntimeState table with default configuration values
This script should be run once to populate the budget configuration in the database
"""

import sys
import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# Add the Backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
load_dotenv(backend_dir / '.env')

from src.core.db import get_session, init_db
from src.db.dbtables import BudgetRuntimeState

def init_budget_config():
    """Initialize or update the BudgetRuntimeState table with default values"""
    session = get_session()
    try:
        # Check if record exists
        state = session.query(BudgetRuntimeState).filter_by(id=1).first()
        
        if state:
            print("✅ BudgetRuntimeState record already exists (id=1)")
            print(f"   Current compare_year: {state.compare_year}")
            print(f"   Current ramadan_cy: {state.ramadan_cy}")
            print(f"   Current ramadan_by: {state.ramadan_by}")
            print("\n🔄 Do you want to update it with new default values? (y/N): ", end='')
            response = input().strip().lower()
            
            if response != 'y':
                print("❌ Cancelled. No changes made.")
                return
            
            # Update existing record
            state.compare_year = 2025
            state.ramadan_cy = date(2025, 3, 1)
            state.ramadan_by = date(2026, 2, 18)
            state.ramadan_daycount_cy = 30
            state.ramadan_daycount_by = 30
            state.muharram_cy = date(2025, 6, 27)
            state.muharram_by = date(2026, 6, 17)
            state.muharram_daycount_cy = 30
            state.muharram_daycount_by = 30
            state.eid2_cy = date(2025, 6, 7)
            state.eid2_by = date(2026, 5, 27)
            
            session.commit()
            print("✅ BudgetRuntimeState updated successfully!")
        else:
            # Create new record with default configuration
            state = BudgetRuntimeState(
                id=1,
                compare_year=2025,
                ramadan_cy=date(2025, 3, 1),
                ramadan_by=date(2026, 2, 18),
                ramadan_daycount_cy=30,
                ramadan_daycount_by=30,
                muharram_cy=date(2025, 6, 27),
                muharram_by=date(2026, 6, 17),
                muharram_daycount_cy=30,
                muharram_daycount_by=30,
                eid2_cy=date(2025, 6, 7),
                eid2_by=date(2026, 5, 27),
                result_json=[]
            )
            session.add(state)
            session.commit()
            print("✅ BudgetRuntimeState created successfully!")
        
        # Display the configuration
        print("\n📊 Current Budget Configuration:")
        print(f"   Compare Year: {state.compare_year}")
        print(f"   Ramadan (CY): {state.ramadan_cy} ({state.ramadan_daycount_cy} days)")
        print(f"   Ramadan (BY): {state.ramadan_by} ({state.ramadan_daycount_by} days)")
        print(f"   Muharram (CY): {state.muharram_cy} ({state.muharram_daycount_cy} days)")
        print(f"   Muharram (BY): {state.muharram_by} ({state.muharram_daycount_by} days)")
        print(f"   Eid al-Adha (CY): {state.eid2_cy}")
        print(f"   Eid al-Adha (BY): {state.eid2_by}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Initializing Budget Configuration...")
    print("=" * 60)
    
    # Initialize database connection first
    print("🔧 Connecting to database...")
    init_db()
    
    init_budget_config()
    print("=" * 60)
    print("✅ Done!")
