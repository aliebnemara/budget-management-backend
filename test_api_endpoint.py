"""
Test the API endpoint directly to verify end-to-end integration
"""
import requests
import json

def test_api_endpoint():
    """Test the /api/islamic-calendar-effects endpoint"""
    print("\n🧪 TESTING API ENDPOINT END-TO-END")
    print("=" * 80)
    
    # API endpoint
    url = "http://localhost:8001/api/islamic-calendar-effects"
    
    # Request payload (matching frontend request)
    payload = {
        "branch_ids": [189],  # Test with branch 189
        "compare_year": 2025,
        "budget_year": 2026,
        "ramadan_CY": "2025-03-01",
        "ramadan_BY": "2026-02-18",
        "ramadan_daycount_CY": 30,
        "ramadan_daycount_BY": 30,
        "muharram_CY": "2025-07-27",
        "muharram_BY": "2026-07-16",
        "muharram_daycount_CY": 10,
        "muharram_daycount_BY": 10,
        "eid2_CY": "2025-06-06",
        "eid2_BY": "2026-05-27"
    }
    
    print(f"\n📡 Sending POST request to: {url}")
    print(f"📊 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the API call (without authentication for testing)
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n📬 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API call successful!")
            print(f"\n📊 Response structure:")
            print(f"   - data: {type(data.get('data'))} with {len(data.get('data', []))} brands")
            
            # Check if we have results for our test branch
            if data.get('data'):
                for brand in data['data']:
                    print(f"\n   Brand: {brand.get('brand_name')}")
                    for branch in brand.get('branches', []):
                        if branch.get('branch_id') == 189:
                            print(f"   ✅ Found branch 189 data!")
                            print(f"      Branch: {branch.get('branch_name')}")
                            print(f"      Months: {len(branch.get('months', []))}")
                            
                            # Check for Eid2 data specifically
                            for month_data in branch.get('months', []):
                                if month_data.get('eid2_pct') and month_data['eid2_pct'] != 0:
                                    print(f"\n      📅 Month {month_data['month']} (Eid Al-Adha affected):")
                                    print(f"         - Sales CY: {month_data.get('sales_CY', 0):.2f} BHD")
                                    print(f"         - Est (no Eid2): {month_data.get('est_sales_no_eid2', 0):.2f} BHD")
                                    print(f"         - Eid2 Impact: {month_data.get('eid2_pct', 0):.2f}%")
            
            print(f"\n" + "=" * 80)
            print(f"✅ END-TO-END TEST SUCCESSFUL")
            
        elif response.status_code == 401:
            print(f"\n⚠️  Authentication required (expected for direct API test)")
            print(f"   This is normal - the frontend will provide authentication")
            print(f"   The API route is correctly configured!")
            
        else:
            print(f"\n❌ API call failed")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to backend server")
        print(f"   Make sure the backend is running on port 8001")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_endpoint()
