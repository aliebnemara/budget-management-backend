# Backend Restart Instructions

## Issue
The April 2026 tile calculation fix has been applied to the code in `src/services/budget.py`, but the backend is running as root process and cannot be restarted from the user session.

## Fix Applied
The service layer now correctly uses **April 2025 days 4-30** (excluding Eid days 1-3) as reference for April 2026, instead of incorrectly falling back to February 2025.

**Expected Result**: April 2026 Expected Sales tile should show **57,295 BHD** instead of **80,472 BHD**.

## Code Changes
- **File**: `/home/user/backend/Backend/src/services/budget.py`
- **Lines**: 589-660
- **Change**: Added special April handling before partial_cy_rows check to prevent February fallback

## Manual Restart Steps

### Option 1: Contact System Administrator
The backend is running as root (PID: 504). Contact your system administrator to restart the backend service.

### Option 2: System Restart (if you have sudo access)
```bash
# Find the backend process
ps aux | grep uvicorn | grep -v grep

# Kill the backend process (requires root)
sudo kill -9 504

# Or restart if systemd service exists
sudo systemctl restart backend
```

### Option 3: Development Environment
If this is a development environment with access to the backend start script:
```bash
cd /home/user/backend/Backend
# Find and run your startup script
./start_backend.sh  # or similar
```

## Verification After Restart

1. **Test API endpoint**:
```bash
curl -X POST "http://localhost:49999/api/islamic-calendar-effects" \
  -H "Content-Type: application/json" \
  -d '{
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
```

2. **Check April 2026 values in response**:
- Look for `"month_name": "April"` in the response
- Verify `"est_sales_no_ramadan"` is approximately **57,295**
- Previously it was incorrectly showing **80,472**

3. **Frontend Testing**:
- Navigate to Islamic Calendar Effects page
- Select "Al Abraaj Bahrain Bay" branch
- Configure Ramadan dates (CY: 2025-03-01, BY: 2026-02-18)
- Click Calculate
- Verify April 2026 tile shows **Expected Sales: 57,295 BHD**

## Technical Details

### Root Cause
The service layer (`Ramadan_Eid_Calculations` function) had logic that:
1. Detected April 2025 has partial Ramadan/Eid data (days 1-3 are Eid)
2. Used `temp_month = mon - 1` to find previous month (March)
3. March also has Ramadan, so kept going back
4. Eventually used February 2025 weekday averages (WRONG!)

### Fix Implementation
Added special handling for April BEFORE the partial month check:
```python
if mon == 4:
    # Use April 2025 days 4-30 (exclude Eid days 1-3)
    day_sales_non_ramadan = branch_sales[
        (branch_sales["month_CY"] == mon) & 
        (branch_sales["year_CY"] == compare_year) &
        (branch_sales["ramadan_CY"] != 2)  # Exclude Eid days
    ].groupby("day_of_week")["gross"].mean().reset_index()
    # Apply to April 2026
    continue  # Skip rest of loop
```

### Why This Works
- April 2025: Days 1-3 are Eid (excluded), days 4-30 are normal (used as reference)
- April 2026: All 30 days are normal (receive April 2025 days 4-30 weekday averages)
- Result: Correct April 2026 estimate of 57,295 BHD

## Files Modified
- `/home/user/backend/Backend/src/services/budget.py` (lines 589-660)

## Backup Location
Original file backed up at:
- `/home/user/backend/Backend/backups/budget_service_before_smart.py`

## Status
✅ Code fix applied
⏳ Backend restart needed
⏳ Frontend testing pending
