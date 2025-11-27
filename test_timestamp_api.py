#!/usr/bin/env python3
"""
Test the last calculation timestamp API endpoint
"""
import requests
import json
from datetime import datetime

print("=" * 80)
print("🧪 TESTING LAST CALCULATION TIMESTAMP API")
print("=" * 80)

# Try to get timestamp without auth first
url = "http://localhost:8000/api/budget/v2/last-calculation-timestamp?budget_year=2026"

print(f"\n📡 Testing endpoint: {url}")

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ SUCCESS - API Response:")
        print(json.dumps(result, indent=2))
        
        if result.get('calculated_at'):
            calculated_at = datetime.fromisoformat(result['calculated_at'].replace('Z', '+00:00'))
            elapsed = result.get('elapsed_seconds', 0)
            
            print(f"\n📊 Parsed Data:")
            print(f"   Calculated at: {calculated_at.strftime('%b %d, %Y, %I:%M:%S %p')}")
            print(f"   Elapsed seconds: {elapsed}")
            
            # Format elapsed time
            if elapsed < 60:
                elapsed_str = f"{elapsed}s"
            elif elapsed < 3600:
                mins = elapsed // 60
                secs = elapsed % 60
                elapsed_str = f"{mins}m {secs}s"
            else:
                hours = elapsed // 3600
                mins = (elapsed % 3600) // 60
                elapsed_str = f"{hours}h {mins}m"
            
            print(f"   Time since: {elapsed_str}")
            
            print(f"\n💡 Frontend will display:")
            print(f"   Last calculated: {calculated_at.strftime('%b %d, %Y, %I:%M:%S %p')} ({elapsed_str})")
            
            print("\n" + "=" * 80)
            print("✅ TIMESTAMP API VERIFIED - Ready for frontend!")
            print("=" * 80)
    elif response.status_code == 401:
        print("\n⚠️  Authentication required - trying with login...")
        
        # Try with login
        login_url = "http://localhost:8000/token"
        login_data = {"username": "admin", "password": "admin123"}
        
        login_response = requests.post(login_url, data=login_data)
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, headers=headers)
            print(f"Status Code (with auth): {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ SUCCESS - API Response:")
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ Failed even with auth: {response.text}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
