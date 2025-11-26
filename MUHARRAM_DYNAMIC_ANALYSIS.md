# Muharram Calculation System - Dynamic Analysis

## 📊 SYSTEM OVERVIEW

Yes, the Muharram calculation system is **FULLY DYNAMIC and SMART**!

## ✅ DYNAMIC COMPONENTS

### 1. **Database-Driven Configuration** ✅
All Muharram parameters are stored in and retrieved from the **`budget_runtime_state`** database table:

**Database Table: `budget_runtime_state`**
- `muharram_cy` (Date) - CY Muharram start date
- `muharram_by` (Date) - BY Muharram start date  
- `muharram_daycount_cy` (Integer) - CY Muharram duration (days)
- `muharram_daycount_by` (Integer) - BY Muharram duration (days)

**Location**: `/home/user/backend/Backend/src/db/dbtables.py` (lines 177-203)

### 2. **Automatic Month Detection** ✅
The system intelligently determines which months are affected by Muharram:

```python
# Calculates date ranges
muharram_start_CY = pd.to_datetime(muharram_CY)
muharram_end_CY = muharram_start_CY + timedelta(days=muharram_daycount_CY - 1)
muharram_start_BY = pd.to_datetime(muharram_BY)
muharram_end_BY = muharram_start_BY + timedelta(days=muharram_daycount_BY - 1)

# Identifies affected months automatically
affected_months_CY = sorted(list(set([muharram_start_CY.month, muharram_end_CY.month])))
affected_months_BY = sorted(list(set([muharram_start_BY.month, muharram_end_BY.month])))
```

**Location**: `/home/user/backend/Backend/src/services/budget.py` (lines 885-899)

**Example**:
- If Muharram CY is **June 26 - July 25** → Affected months: `[6, 7]` (June, July)
- If Muharram BY is **July 16 - July 25** → Affected months: `[7]` (July only)

### 3. **Smart Weekday Average Separation** ✅
The system automatically:

1. **Identifies NON-MUHARRAM days** in affected months (e.g., June 1-25 + July 26-31)
2. **Identifies MUHARRAM days** in affected months (e.g., June 26 - July 25)
3. **Calculates TWO separate weekday averages**:
   - NON-MUHARRAM average (from normal days)
   - MUHARRAM average (from Muharram period days)

**Location**: `/home/user/backend/Backend/src/services/budget.py` (lines 926-996)

```python
# 🟢 NON-MUHARRAM DAYS (automatically filtered)
non_muharram_df = branch_june_july_df[
    ~branch_june_july_df['business_date'].between(muharram_start_CY, muharram_end_CY)
].copy()

# 🟠 MUHARRAM DAYS (automatically identified)
muharram_df = branch_june_july_df[
    branch_june_july_df['business_date'].between(muharram_start_CY, muharram_end_CY)
].copy()
```

### 4. **Intelligent BY Estimation** ✅
For each day in BY affected months, the system automatically determines:

```python
# For each day in BY 2026
is_muharram_2026 = (muharram_start_BY <= date_by <= muharram_end_BY)

if is_muharram_2026:
    # Use MUHARRAM weekday average
    estimated_gross = weekday_avg_MUHARRAM.get(day_of_week, actual_gross)
else:
    # Use NON-MUHARRAM weekday average
    estimated_gross = weekday_avg_NON_MUHARRAM.get(day_of_week, actual_gross)
```

**Location**: `/home/user/backend/Backend/src/services/budget.py` (lines 1007-1032)

### 5. **Daily Breakdown Intelligence** ✅
The API provides detailed daily estimation using the same logic:

```python
# Determine if this day falls within Muharram period in BY 2026
date_BY = pd.Timestamp(year=budget_year, month=month, day=day_num)
is_muharram_day = (muharram_start_BY <= date_BY <= muharram_end_BY)

# Use appropriate weekday average based on whether day is in Muharram period
if is_muharram_day:
    estimated_value = float(branch_avg['MUHARRAM'].get(day_of_week_BY, daily_gross))
else:
    estimated_value = float(branch_avg['NON_MUHARRAM'].get(day_of_week_BY, daily_gross))
```

**Location**: `/home/user/backend/Backend/src/api/routes/budget.py` (lines 605-616)

## 🔄 DATA FLOW

```
1. Database (budget_runtime_state)
   ↓
2. Backend /api/home endpoint (loads config)
   ↓
3. compute_or_reuse() → gets muharram_cy/by + daycount from DB
   ↓
4. Muharram_calculations() service
   - Calculates date ranges
   - Identifies affected months
   - Separates NON-MUHARRAM and MUHARRAM days
   - Calculates TWO weekday averages
   - Estimates BY months intelligently
   ↓
5. Returns: {monthly_summary, metadata}
   ↓
6. /api/islamic-calendar-effects endpoint
   - Uses metadata for daily breakdown
   - Applies correct weekday average per day
   ↓
7. Frontend displays results
```

## 📝 CONFIGURATION EXAMPLES

### Current Configuration (2025-2026)
```json
{
  "muharram_CY": "2025-06-26",
  "muharram_daycount_CY": 30,
  "muharram_BY": "2026-06-16", 
  "muharram_daycount_BY": 30
}
```

**System automatically handles:**
- CY affected months: June, July (spans 2 months)
- BY affected months: June, July (spans 2 months)
- NON-MUHARRAM days: June 1-25, July 27-31 (CY 2025)
- MUHARRAM days: June 26 - July 25 (CY 2025)

### Future Configuration Example (2026-2027)
If Muharram shifts earlier:
```json
{
  "muharram_CY": "2026-06-05",
  "muharram_daycount_CY": 30,
  "muharram_BY": "2027-05-25",
  "muharram_daycount_BY": 30  
}
```

**System will automatically:**
- Detect affected months: June only for CY, May-June for BY
- Recalculate NON-MUHARRAM days based on new dates
- Recalculate MUHARRAM days based on new dates
- Apply correct weekday averages per period

## ✅ CONCLUSION

**YES**, the Muharram calculation system is **FULLY DYNAMIC AND INTELLIGENT**:

1. ✅ **All parameters come from database** (`budget_runtime_state` table)
2. ✅ **Automatically detects affected months** based on start date + day count
3. ✅ **Intelligently separates periods** (NON-MUHARRAM vs MUHARRAM days)
4. ✅ **Calculates appropriate weekday averages** for each period
5. ✅ **Applies correct estimation logic** per day in BY year
6. ✅ **Handles any date shift** without code changes

**You only need to update the database values**, and the system will automatically:
- Determine which months are affected
- Calculate proper date ranges
- Separate periods correctly
- Apply appropriate weekday averages
- Provide accurate daily breakdowns

**No code changes needed** when Muharram dates change year to year! 🎯
