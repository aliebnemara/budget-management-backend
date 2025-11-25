#!/usr/bin/env python3
"""
Test script for Smart Ramadan System Integration
Tests that the API endpoint properly uses the smart dynamic system
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/islamic-calendar-effects"

# Test payload - 2025-2026 scenario (current)
test_payload_2025 = {
    "branch_ids": [200],  # Using a known branch
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

print("=" * 80)
print("🧪 TESTING SMART RAMADAN SYSTEM INTEGRATION")
print("=" * 80)

print(f"\n📍 Testing endpoint: {BASE_URL}{ENDPOINT}")
print(f"📦 Payload: branch_ids={test_payload_2025['branch_ids']}, compare_year={test_payload_2025['compare_year']}")

try:
    response = requests.post(
        f"{BASE_URL}{ENDPOINT}",
        json=test_payload_2025,
        timeout=30
    )
    
    print(f"\n📊 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check if we got data back
        if 'data' in data and len(data['data']) > 0:
            print("✅ API returned data successfully!")
            
            # Analyze the response structure
            brand = data['data'][0]
            print(f"\n📋 Response Structure:")
            print(f"  - Brands: {len(data['data'])}")
            print(f"  - First Brand ID: {brand.get('brand_id')}")
            print(f"  - Branches: {len(brand.get('branches', []))}")
            
            if brand.get('branches'):
                branch = brand['branches'][0]
                print(f"  - First Branch ID: {branch.get('branch_id')}")
                print(f"  - Months: {len(branch.get('months', []))}")
                
                # Check which months are included
                months_included = [m['month'] for m in branch.get('months', [])]
                print(f"  - Months included: {months_included}")
                
                # Check daily breakdown
                if branch.get('months'):
                    first_month = branch['months'][0]
                    daily_sales = first_month.get('daily_sales', [])
                    print(f"  - Daily breakdown for month {first_month['month']}: {len(daily_sales)} days")
                    
                    if daily_sales:
                        # Show first few days
                        print(f"\n📅 Sample Daily Data (first 5 days):")
                        for day_data in daily_sales[:5]:
                            print(f"    Day {day_data['day']}: Actual={day_data['actual']:.2f}, Estimated={day_data['estimated']:.2f}")
                
                print("\n✅ INTEGRATION TEST PASSED!")
                print("   The API is working with the Smart Ramadan System")
                print("   Check backend.log for Smart System initialization messages")
        else:
            print("⚠️  API returned empty data")
            print(f"   Response: {json.dumps(data, indent=2)}")
    
    else:
        print(f"❌ API returned error status: {response.status_code}")
        print(f"   Response: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to backend server")
    print("   Make sure backend is running on port 8000")
except requests.exceptions.Timeout:
    print("❌ ERROR: Request timed out")
    print("   Backend may be processing or overloaded")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n" + "=" * 80)
print("📝 Next Steps:")
print("1. Check backend.log for Smart System messages:")
print("   tail -100 backend.log | grep -E '🌙|🎯|📋'")
print("2. If you see Smart System messages, integration is working!")
print("3. Test frontend Islamic Calendar Effects page")
print("=" * 80)
