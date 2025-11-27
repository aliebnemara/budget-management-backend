#!/usr/bin/env python3
"""
Test the API to verify daily_sales array is returned correctly
"""
import requests
import json

print("=" * 80)
print("🧪 TESTING DAILY_SALES API FIX")
print("=" * 80)

# Login first
login_url = "http://localhost:8000/login"
login_data = {"username": "admin", "password": "admin123"}

try:
    login_response = requests.post(login_url, data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed. Trying token endpoint...")
        # Try alternative auth
        token_url = "http://localhost:8000/token"
        login_response = requests.post(token_url, data=login_data)
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print("❌ No access token in response")
            print(json.dumps(token_data, indent=2))
            exit(1)
        
        print(f"✅ Logged in successfully")
        
        # Test the Islamic calendar effects V2 API
        url = "http://localhost:8000/api/budget/v2/islamic-calendar-effects"
        payload = {
            "branch_ids": [189],
            "compare_year": 2025,
            "budget_year": 2026,
            "months": [2],  # Just February
            "ramadan_CY": "2025-03-01",
            "muharram_CY": "2025-06-27",
            "eid2_CY": "2025-06-06"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\n📡 API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Navigate to the first branch's February data
            if result.get('data') and len(result['data']) > 0:
                first_brand = result['data'][0]
                if first_brand.get('branches') and len(first_brand['branches']) > 0:
                    first_branch = first_brand['branches'][0]
                    feb_data = next((m for m in first_branch.get('months', []) if m['month'] == 2), None)
                    
                    if feb_data:
                        print(f"\n✅ February 2026 Data:")
                        print(f"   Branch ID: {first_branch['branch_id']}")
                        print(f"   Sales_CY: {feb_data.get('sales_CY')}")
                        print(f"   Ramadan %: {feb_data.get('ramadan_eid_pct')}")
                        
                        # Check for daily_sales array
                        daily_sales = feb_data.get('daily_sales')
                        if daily_sales:
                            print(f"\n✅ daily_sales array found! Length: {len(daily_sales)}")
                            print(f"\n📊 First 5 days:")
                            for day in daily_sales[:5]:
                                print(f"   Day {day.get('day'):2d}: Date={day.get('date')} | Actual={day.get('actual'):8.2f} | Estimated={day.get('estimated'):8.2f}")
                            
                            print(f"\n📊 Last 3 days:")
                            for day in daily_sales[-3:]:
                                print(f"   Day {day.get('day'):2d}: Date={day.get('date')} | Actual={day.get('actual'):8.2f} | Estimated={day.get('estimated'):8.2f}")
                            
                            # Verify totals
                            total_actual = sum(d.get('actual', 0) for d in daily_sales)
                            total_estimated = sum(d.get('estimated', 0) for d in daily_sales)
                            
                            print(f"\n💰 Verification:")
                            print(f"   Total Actual (sum of daily): {total_actual:,.2f}")
                            print(f"   sales_CY (from API): {feb_data.get('sales_CY'):,.2f}")
                            print(f"   Match: {'✅ YES' if abs(total_actual - feb_data.get('sales_CY', 0)) < 0.01 else '❌ NO'}")
                            
                            print("\n" + "=" * 80)
                            print("✅ FIX VERIFIED - daily_sales array is working!")
                            print("=" * 80)
                        else:
                            print(f"\n❌ daily_sales array is MISSING!")
                            print(f"   Keys in month data: {list(feb_data.keys())}")
                    else:
                        print("❌ February data not found")
                else:
                    print("❌ No branches in response")
            else:
                print("❌ No data in response")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text[:500])
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
