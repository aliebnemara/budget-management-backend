#!/bin/bash

# Test April 2026 Fix - Islamic Calendar Effects API
# This script tests if the April 2026 tile calculation fix is working correctly

echo "=========================================="
echo "Testing April 2026 Fix"
echo "=========================================="
echo ""

# API endpoint
API_URL="http://localhost:49999/api/islamic-calendar-effects"

# Test payload
PAYLOAD='{
  "budget_year": 2026,
  "compare_year": 2025,
  "branch_name": "Al Abraaj Bahrain Bay",
  "ramadan_setup": {
    "ramadan_CY": "2025-03-01",
    "ramadan_BY": "2026-02-18",
    "ramadan_daycount_CY": 30,
    "ramadan_daycount_BY": 30
  }
}'

echo "📡 Calling Islamic Calendar Effects API..."
echo "Branch: Al Abraaj Bahrain Bay"
echo "Budget Year: 2026 | Compare Year: 2025"
echo ""

# Make API call and save response
RESPONSE=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# Check if API call was successful
if [ $? -ne 0 ]; then
    echo "❌ API call failed!"
    exit 1
fi

echo "✅ API call successful"
echo ""

# Extract April 2026 values using Python
python3 << 'PYTHON_SCRIPT'
import json
import sys

try:
    # Read response from stdin
    response = json.loads('''RESPONSE''')
    
    # Check if response has data
    if 'data' not in response:
        print("❌ No data in response")
        sys.exit(1)
    
    data = response['data']
    
    # Find April 2026
    april_data = None
    for month_data in data:
        if month_data.get('month_name') == 'April' and month_data.get('year') == 2026:
            april_data = month_data
            break
    
    if not april_data:
        print("❌ April 2026 not found in response")
        sys.exit(1)
    
    # Extract values
    expected_sales = april_data.get('est_sales_no_ramadan', 0)
    actual_sales = april_data.get('actual_gross', 0)
    
    print("========================================")
    print("April 2026 Values:")
    print("========================================")
    print(f"Expected Sales (est_sales_no_ramadan): {expected_sales:,.2f} BHD")
    print(f"Actual Sales: {actual_sales:,.2f} BHD")
    print("")
    
    # Check if fix is working
    EXPECTED_VALUE = 57295
    TOLERANCE = 100  # Allow small rounding differences
    
    if abs(expected_sales - EXPECTED_VALUE) <= TOLERANCE:
        print("✅ FIX VERIFIED!")
        print(f"   Expected Sales matches target: ~{EXPECTED_VALUE:,} BHD")
        print("")
        print("🎉 The service layer fix is working correctly!")
        print("   April 2026 now uses April 2025 days 4-30 as reference")
    else:
        print("❌ FIX NOT WORKING")
        print(f"   Expected: ~{EXPECTED_VALUE:,} BHD")
        print(f"   Got: {expected_sales:,.2f} BHD")
        print("")
        if abs(expected_sales - 80472) <= TOLERANCE:
            print("⚠️  Still using old logic (February 2025 reference)")
            print("   Backend needs to be restarted to load new code")
        else:
            print("⚠️  Unexpected value - needs investigation")
    
    print("")
    print("========================================")
    
except json.JSONDecodeError as e:
    print(f"❌ Failed to parse JSON response: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. If fix verified: Commit changes to GitHub"
echo "2. If fix not working: Backend needs restart (see RESTART_BACKEND.md)"
echo "3. Test other months (Feb, Mar) to ensure no regression"
echo "4. Test frontend Islamic Calendar Effects page"
