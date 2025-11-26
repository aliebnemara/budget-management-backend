"""
Check current Eid Al-Adha configuration from database
"""
import sys
import os
sys.path.append('/home/user/backend/Backend/src')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/home/user/backend/Backend/.env')

from src.core.db import init_db, get_session, close_session
from src.db.dbtables import BudgetRuntimeState

def check_eid2_config():
    """Check current Eid Al-Adha dates in database"""
    # Initialize database connection
    init_db()
    dbs = get_session()
    try:
        # Get the budget runtime state
        runtime_state = dbs.query(BudgetRuntimeState).first()
        
        if not runtime_state:
            print("❌ No runtime state found in database")
            return
        
        print("\n📋 CURRENT EID AL-ADHA CONFIGURATION")
        print("=" * 60)
        print(f"CY Eid Al-Adha Date: {runtime_state.eid2_cy}")
        print(f"BY Eid Al-Adha Date: {runtime_state.eid2_by}")
        print()
        
        # Analyze month shift
        cy_month = runtime_state.eid2_cy.month
        by_month = runtime_state.eid2_by.month
        
        print(f"CY Month: {cy_month} ({runtime_state.eid2_cy.strftime('%B %Y')})")
        print(f"BY Month: {by_month} ({runtime_state.eid2_by.strftime('%B %Y')})")
        print()
        
        if cy_month == by_month:
            print("✅ SAME MONTH DETECTED")
            print("   → Expected Impact: 0% (No calculation)")
        else:
            print("🔄 MONTH SHIFT DETECTED")
            print(f"   → CY: Month {cy_month} → BY: Month {by_month}")
            print("   → Expected: Impact calculation with Eid day copying by number")
        
        print("=" * 60)
        
    finally:
        close_session(dbs)

if __name__ == "__main__":
    check_eid2_config()
