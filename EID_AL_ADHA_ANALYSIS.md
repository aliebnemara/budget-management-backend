# Eid Al-Adha (Eid2) Calculation System - Analysis

## 📊 SYSTEM OVERVIEW

Eid Al-Adha (referred to as "Eid2" in code) calculation is **simpler than Muharram** as it focuses on tracking **EID DAY SHIFT** only, not extended periods.

## 🎯 CURRENT IMPLEMENTATION

### 1. **Database Configuration** ✅
Eid2 parameters are stored in `budget_runtime_state` table:

**Database Fields:**
- `eid2_cy` (Date) - CY Eid Al-Adha date (e.g., 2025-06-06)
- `eid2_by` (Date) - BY Eid Al-Adha date (e.g., 2026-05-27)
- **Note**: NO day count field (unlike Ramadan/Muharram) - uses fixed 3-day period

**Location**: `/home/user/backend/Backend/src/db/dbtables.py` (lines 192-193)

### 2. **Current Logic Overview**
The `Eid2Calculations()` function treats Eid2 as a **3-day event**:

```python
def Eid2Calculations(compare_year, eid2_CY, eid2_BY, df):
    muharram_periods = {
        year: (start, start + timedelta(days=2))  # 3 days total (Day 0, 1, 2)
        for year, start in muharram_start_dates.items()
    }
```

**Location**: `/home/user/backend/Backend/src/services/budget.py` (lines 721-867)

### 3. **Day Categorization Logic**
The function assigns flags to each date:

```python
def assign_muharram_flag(date):
    if muharram_start <= date <= muharram_end:
        return 1  # Eid day itself (3 days: Eid Day 0, 1, 2)
    elif date.month == muharram_start.month or date.month == muharram_end.month:
        return 3  # Same month as Eid (but not Eid days)
    elif date.month == muharram_end_c.month and year == compare_year + 1:
        return 3  # Handle cross-month scenario
    return 0  # Normal day
```

**Categories**:
- **Flag 1**: Eid days (3 consecutive days starting from Eid date)
- **Flag 3**: Non-Eid days in affected months
- **Flag 0**: Normal days (not in Eid months)

**Location**: Lines 736-747

### 4. **Estimation Strategy**

**For BY Eid Days (Flag 1)**:
```python
# Calculate average of CY Eid days by weekday
day_sales_muharram = branch_sales[branch_sales["muharram_CY"] == 1].groupby(
    "day_of_week")["gross"].mean().reset_index()

# Apply to BY Eid days based on weekday
for _, v in day_sales_muharram.iterrows():
    branch_sales.loc[(branch_sales["muharram_BY"] == 1) & (
        branch_sales["day_of_week_BY"] == v["day_of_week"]), "gross_BY"] = v["gross"]
```

**Logic**: 
- Take CY Eid days (3 days) → Calculate weekday averages
- Apply these averages to BY Eid days based on matching weekday

**Location**: Lines 795-799

**For Non-Eid Days in Affected Months (Flag 3)**:
- Uses weekday averaging from previous month or same month (similar to Muharram logic)

**Location**: Lines 801-848

## 📅 CURRENT CONFIGURATION EXAMPLE

### CY 2025: Eid2 = June 6, 2025
- **Eid Days**: June 6, 7, 8 (3 days) - Friday, Saturday, Sunday
- **Affected Month**: June (month 6)
- **Non-Eid June Days**: June 1-5, June 9-30

### BY 2026: Eid2 = May 27, 2026
- **Eid Days**: May 27, 28, 29 (3 days) - Wednesday, Thursday, Friday  
- **Affected Month**: May (month 5)
- **Non-Eid May Days**: May 1-26, May 30-31

### Date Shift Impact
- **Shift**: 10 days earlier (June 6 → May 27)
- **Month Change**: June → May
- **Weekday Change**: Fri/Sat/Sun → Wed/Thu/Fri

## 🔍 KEY DIFFERENCES FROM MUHARRAM

| Feature | Muharram | Eid Al-Adha |
|---------|----------|-------------|
| **Duration** | 30 days (configurable via daycount) | **3 days (hardcoded)** |
| **Database Fields** | muharram_cy/by + daycount_cy/by | **eid2_cy/by only** |
| **Affected Period** | Long period (30 days) | **Short event (3 days)** |
| **Month Span** | Often spans 2 months | **Usually 1 month** |
| **Weekday Averages** | TWO separate (NON-MUHARRAM vs MUHARRAM) | **ONE (Eid days only)** |
| **Complexity** | High (period separation) | **Lower (event tracking)** |
| **Daily Analysis** | Required (30 days) | **Simple (3 days)** |

## ⚠️ CURRENT LIMITATIONS & OBSERVATIONS

### 1. **Hardcoded 3-Day Duration**
```python
muharram_periods = {
    year: (start, start + timedelta(days=2))  # Always 3 days
}
```
- No flexibility for different Eid durations
- No `eid2_daycount_cy` or `eid2_daycount_by` in database

### 2. **Confusing Variable Names**
```python
# Function is called Eid2Calculations but uses "muharram" variable names
muharram_start_dates = { ... }  # Should be "eid2_start_dates"
muharram_periods = { ... }      # Should be "eid2_periods"
assign_muharram_flag()          # Should be "assign_eid2_flag"
```
This creates confusion when reading the code.

### 3. **Simple Month Logic**
- Assumes Eid stays within 1-2 months
- Doesn't handle complex cross-month scenarios
- Unlike Muharram which has sophisticated month detection

### 4. **Single Weekday Average**
- Only calculates average for Eid days (Flag 1)
- Non-Eid days (Flag 3) use previous month logic
- Unlike Muharram which separates NON-MUHARRAM vs MUHARRAM averages

## ✅ WHAT WORKS WELL

1. **Database-Driven Dates** ✅
   - `eid2_cy` and `eid2_by` come from database
   - Easy to update for different years

2. **Simple Event Tracking** ✅
   - 3-day window is easy to understand
   - Clear Eid day identification

3. **Weekday-Based Estimation** ✅
   - Matches Eid days by weekday between years
   - Handles weekday shift automatically

4. **Month Impact Calculation** ✅
   - Calculates impact percentage for affected months
   - Returns monthly summary similar to Muharram

## 🎯 POSSIBLE IMPROVEMENTS (NOT IMPLEMENTING)

### 1. Make Duration Configurable
- Add `eid2_daycount_cy` and `eid2_daycount_by` to database
- Replace hardcoded `timedelta(days=2)` with variable duration

### 2. Rename Variables for Clarity
- Change "muharram" variable names to "eid2"
- Make code more maintainable and less confusing

### 3. Enhanced Month Detection
- Use similar logic to Muharram for automatic month detection
- Handle complex cross-month scenarios better

### 4. Two-Tier Weekday Averaging
- Separate "Eid period" vs "Non-Eid period" like Muharram
- More accurate estimation for non-Eid days in affected months

## 📊 CURRENT DATA FLOW

```
1. Database (budget_runtime_state)
   - eid2_cy, eid2_by
   ↓
2. Backend /api/home or /api/islamic-calendar-effects
   - Loads eid2 dates from request or database
   ↓
3. Eid2Calculations() service
   - Creates 3-day periods (hardcoded)
   - Assigns flags (1=Eid, 3=Same month, 0=Normal)
   - Calculates weekday average for Eid days (Flag 1)
   - Estimates BY based on weekday matching
   ↓
4. Returns: monthly_summary DataFrame
   - branch_id, month, actual, est, Eid2 %
   ↓
5. Frontend displays impact (no detailed daily breakdown currently)
```

## 🔧 CONFIGURATION UPDATE PROCESS

**To update Eid Al-Adha dates for new years:**

1. Update `budget_runtime_state` table:
   ```sql
   UPDATE budget_runtime_state 
   SET eid2_cy = '2026-05-27',
       eid2_by = '2027-05-17'
   WHERE id = 1;
   ```

2. System automatically:
   ✅ Creates 3-day period for each date
   ✅ Identifies affected months
   ✅ Calculates weekday averages
   ✅ Estimates BY Eid days based on weekday

3. **No code changes needed** ✅

## ✅ CONCLUSION

**Eid Al-Adha system is PARTIALLY DYNAMIC:**

1. ✅ **Dates come from database** (eid2_cy, eid2_by)
2. ✅ **Basic shift tracking works** (3-day event)
3. ✅ **Weekday-based estimation** (matches days by weekday)
4. ⚠️  **Duration is hardcoded** (always 3 days)
5. ⚠️  **Simple month logic** (not as sophisticated as Muharram)
6. ⚠️  **Confusing variable names** (uses "muharram" names for Eid2)

**Key Insight**: Eid Al-Adha is treated as a **simple 3-day event shift**, not a complex period like Muharram. This makes it easier to track but less flexible.

**Question for Discussion**: Should Eid Al-Adha duration be configurable like Ramadan/Muharram? Or is the fixed 3-day period sufficient for business needs? 🤔
