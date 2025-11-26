"""
Test Eid2Calculations_v2 function with current database configuration
"""
import sys
import os
import pandas as pd
from datetime import datetime
sys.path.append('/home/user/backend/Backend/src')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/home/user/backend/Backend/.env')

from src.core.db import init_db, get_session, close_session
from src.db.dbtables import BudgetRuntimeState
from src.services.budget import Eid2Calculations_v2

def test_eid2_v2():
    """Test the new Eid2Calculations_v2 function"""
    print("\n🧪 TESTING EID2CALCULATIONS_V2 FUNCTION")
    print("=" * 80)
    
    # Initialize database
    init_db()
    dbs = get_session()
    
    try:
        # Get configuration from database
        runtime_state = dbs.query(BudgetRuntimeState).first()
        if not runtime_state:
            print("❌ No runtime state found")
            return
        
        compare_year = 2025
        eid2_CY = runtime_state.eid2_cy
        eid2_BY = runtime_state.eid2_by
        
        print(f"\n📅 Configuration:")
        print(f"   Compare Year: {compare_year}")
        print(f"   CY Eid: {eid2_CY} (Month {eid2_CY.month})")
        print(f"   BY Eid: {eid2_BY} (Month {eid2_BY.month})")
        
        # Load data
        print(f"\n📊 Loading BaseData.pkl...")
        df = pd.read_pickle('/home/user/backend/Backend/BaseData.pkl')
        print(f"   Total rows: {len(df):,}")
        print(f"   Date range: {df['business_date'].min()} to {df['business_date'].max()}")
        print(f"   Unique branches: {df['branch_id'].nunique()}")
        
        # Test with a single branch first for clarity
        test_branch_id = 189
        df_test = df[df['branch_id'] == test_branch_id].copy()
        print(f"\n🔍 Testing with branch {test_branch_id}")
        print(f"   Branch data rows: {len(df_test):,}")
        
        # Run the calculation
        print(f"\n🚀 Running Eid2Calculations_v2...")
        result = Eid2Calculations_v2(compare_year, eid2_CY, eid2_BY, df_test)
        
        print(f"\n📊 RESULTS:")
        print("=" * 80)
        
        if result.empty:
            print("❌ No results returned")
            return
        
        print(f"\nTotal result rows: {len(result)}")
        print(f"\nResult columns: {result.columns.tolist()}")
        print(f"\nResult data:")
        print(result.to_string())
        
        # Analyze results
        print(f"\n📈 ANALYSIS:")
        print("=" * 80)
        
        for _, row in result.iterrows():
            month = int(row['month'])
            impact_pct = float(row['Eid2 %'])
            actual = float(row['actual'])
            est = float(row['est'])
            
            print(f"\n📅 Month {month}:")
            print(f"   Branch ID: {int(row['branch_id'])}")
            print(f"   Actual (CY): {actual:,.2f}")
            print(f"   Estimated (BY): {est:,.2f}")
            print(f"   Impact: {impact_pct:.2f}%")
            
            if impact_pct == 0:
                print(f"   ✅ Same month detected - no calculation (as expected)")
            else:
                print(f"   🔄 Impact calculated using Eid day copying by number")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        close_session(dbs)

if __name__ == "__main__":
    test_eid2_v2()
