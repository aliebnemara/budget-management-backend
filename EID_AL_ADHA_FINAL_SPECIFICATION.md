# Eid Al-Adha Calculation System - FINAL SPECIFICATION

**Document Version**: 1.0 Final  
**Date**: November 26, 2025  
**Status**: Ready for Implementation  
**Author**: Budget Management System Team

---

## 📋 TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Core Concept](#core-concept)
3. [Business Logic](#business-logic)
4. [Calculation Methodology](#calculation-methodology)
5. [Implementation Requirements](#implementation-requirements)
6. [Examples](#examples)
7. [Comparison with Other Islamic Events](#comparison)

---

## 1. EXECUTIVE SUMMARY

### Purpose
This document defines the complete business logic and calculation methodology for Eid Al-Adha impact analysis in the Budget Management System.

### Key Principle
**Eid Al-Adha tracks MONTH SHIFT of a 3-day event.**

### Decision Tree
```
Is Eid in SAME month in CY and BY?
├─ YES → NO CALCULATION (Impact = 0%)
└─ NO  → CALCULATE IMPACT (Eid shifted to different month)
```

### Database Configuration
- **Table**: `budget_runtime_state`
- **Fields**: 
  - `eid2_cy` (Date) - CY Eid Al-Adha start date
  - `eid2_by` (Date) - BY Eid Al-Adha start date
- **Duration**: Fixed 3 days (hardcoded, not in database)

---

## 2. CORE CONCEPT

### 2.1 What We Track
Eid Al-Adha is a **3-day event** that shifts annually according to the Islamic lunar calendar. We track whether this event **moves to a different month** between Compare Year (CY) and Budget Year (BY).

### 2.2 Why Month Shift Matters
When Eid moves to a different month:
- **Month that loses Eid** (CY month) shows negative impact
- **Month that gains Eid** (BY month) shows positive impact
- **Other months** are not affected by this specific event

### 2.3 The Three Eid Days
Eid Al-Adha consists of three consecutive days:
- **Eid Day 1**: Main celebration day (typically highest sales)
- **Eid Day 2**: Second day continuation
- **Eid Day 3**: Third day continuation

**Critical Point**: These are **EVENT days**, not weekdays. Eid Day 1 has its own sales pattern regardless of whether it falls on Friday, Wednesday, or any other weekday.

---

## 3. BUSINESS LOGIC

### 3.1 SCENARIO 1: Same Month (NO IMPACT)

#### Condition
```
eid2_CY.month == eid2_BY.month
```

#### Action
- **NO calculation performed**
- **NO estimation needed**
- **Return**: Impact = 0%

#### Display Message
```
"Eid Al-Adha falls in the same month in both years"
"No positive or negative sales effect"
Month Impact: 0%
```

#### Example
```
CY 2025: Eid = June 15, 16, 17 (Month: 6)
BY 2026: Eid = June 4, 5, 6   (Month: 6)

Result: Same month (6 == 6)
Action: Display "No impact" message
Impact: 0%
```

---

### 3.2 SCENARIO 2: Different Month (CALCULATE IMPACT)

#### Condition
```
eid2_CY.month != eid2_BY.month
```

#### Action
- **Identify affected months** in CY and BY
- **Calculate Eid day sales** for each affected month
- **Calculate non-Eid day sales** for each affected month
- **Estimate BY sales** using correct methodology
- **Return**: Impact percentage per affected month

#### Example
```
CY 2025: Eid = June 6, 7, 8 (Month: 6)
BY 2026: Eid = May 27, 28, 29 (Month: 5)

Result: Different months (6 != 5)
Action: Calculate impact for June (CY) and May (BY)
```

---

## 4. CALCULATION METHODOLOGY

### 4.1 Step 1: Detect Month Shift

```python
cy_eid_start = eid2_CY  # e.g., 2025-06-06
cy_eid_end = eid2_CY + timedelta(days=2)  # e.g., 2025-06-08

by_eid_start = eid2_BY  # e.g., 2026-05-27
by_eid_end = eid2_BY + timedelta(days=2)  # e.g., 2026-05-29

# Identify affected months
cy_affected_months = sorted(list(set([cy_eid_start.month, cy_eid_end.month])))
by_affected_months = sorted(list(set([by_eid_start.month, by_eid_end.month])))

# Check if month shift occurred
if cy_affected_months == by_affected_months:
    return "No impact - Same month"
else:
    proceed_with_calculation()
```

---

### 4.2 Step 2: Handle Two Cases

#### CASE A: Eid Within ONE Month (Simpler)

**CY Month Breakdown**:
```
Month: June 2025 (30 days total)
├─ Eid Days: June 6, 7, 8 (3 days)
│   ├─ Eid Day 1: June 6 (Friday): 5,000 BHD
│   ├─ Eid Day 2: June 7 (Saturday): 6,000 BHD
│   └─ Eid Day 3: June 8 (Sunday): 4,500 BHD
│   Total Eid Sales: 15,500 BHD
│
└─ Non-Eid Days: June 1-5, 9-30 (27 days)
    Calculate weekday averages from these 27 days:
    ├─ Monday avg: 3,000 BHD (from 4 Mondays)
    ├─ Tuesday avg: 2,800 BHD (from 4 Tuesdays)
    ├─ Wednesday avg: 2,900 BHD (from 4 Wednesdays)
    ├─ Thursday avg: 3,100 BHD (from 4 Thursdays)
    ├─ Friday avg: 3,500 BHD (from 3 Fridays - excluding Eid Day 1)
    ├─ Saturday avg: 4,000 BHD (from 3 Saturdays - excluding Eid Day 2)
    └─ Sunday avg: 3,200 BHD (from 3 Sundays - excluding Eid Day 3)
    Total Non-Eid Sales: 87,000 BHD (example)
```

**BY Month Estimation**:
```
Month: May 2026 (31 days total)
├─ Eid Days: May 27, 28, 29 (3 days)
│   ├─ Eid Day 1: May 27 (Wednesday) → 5,000 BHD (from CY Eid Day 1)
│   ├─ Eid Day 2: May 28 (Thursday) → 6,000 BHD (from CY Eid Day 2)
│   └─ Eid Day 3: May 29 (Friday) → 4,500 BHD (from CY Eid Day 3)
│   Total Eid Sales: 15,500 BHD (exact copy from CY)
│
└─ Non-Eid Days: May 1-26, 30-31 (28 days)
    Apply CY non-Eid weekday averages to each day:
    ├─ May 5 (Monday) → 3,000 BHD
    ├─ May 6 (Tuesday) → 2,800 BHD
    ├─ May 7 (Wednesday) → 2,900 BHD
    └─ ... (continue for all 28 non-Eid days)
    Total Non-Eid Sales: 89,000 BHD (estimated)
```

**Month Impact Calculation**:
```
CY June Total: 15,500 + 87,000 = 102,500 BHD
BY May Total: 15,500 + 89,000 = 104,500 BHD
Impact: (104,500 - 102,500) / 102,500 × 100 = +1.95%
```

---

#### CASE B: Eid Spans TWO Months (More Complex)

**Scenario**: Eid starts in one month and ends in the next

**CY Month Breakdown**:
```
June 2025 (30 days):
├─ Eid Days: June 29, 30 (2 days)
│   ├─ Eid Day 1: June 29 (Sunday): 5,000 BHD
│   └─ Eid Day 2: June 30 (Monday): 6,000 BHD
│   Subtotal: 11,000 BHD
│
└─ Non-Eid Days: June 1-28 (28 days)
    Calculate weekday averages from these 28 days
    Subtotal: 85,000 BHD (example)

July 2025 (31 days):
├─ Eid Days: July 1 (1 day)
│   └─ Eid Day 3: July 1 (Tuesday): 4,500 BHD
│   Subtotal: 4,500 BHD
│
└─ Non-Eid Days: July 2-31 (30 days)
    Calculate weekday averages from these 30 days
    Subtotal: 90,000 BHD (example)
```

**BY Month Estimation**:
```
May 2026 (31 days):
├─ Eid Days: May 30, 31 (2 days)
│   ├─ Eid Day 1: May 30 (Saturday) → 5,000 BHD (from CY Eid Day 1)
│   └─ Eid Day 2: May 31 (Sunday) → 6,000 BHD (from CY Eid Day 2)
│   Subtotal: 11,000 BHD
│
└─ Non-Eid Days: May 1-29 (29 days)
    Apply CY MAY non-Eid weekday averages
    Subtotal: 87,000 BHD (estimated)

June 2026 (30 days):
├─ Eid Days: June 1 (1 day)
│   └─ Eid Day 3: June 1 (Monday) → 4,500 BHD (from CY Eid Day 3)
│   Subtotal: 4,500 BHD
│
└─ Non-Eid Days: June 2-30 (29 days)
    Apply CY JUNE non-Eid weekday averages
    Subtotal: 87,000 BHD (estimated)
```

**Critical Rule for Case B**:
- **Each BY month uses its SAME month's CY non-Eid averages**
- **BY May non-Eid days** → Apply **CY May non-Eid averages** (minimum 26 days available)
- **BY June non-Eid days** → Apply **CY June non-Eid averages** (minimum 26 days available)
- **BY July non-Eid days** → Apply **CY July non-Eid averages** (minimum 26 days available)
- Each month has sufficient non-Eid days (minimum 26) to calculate reliable weekday averages

---

### 4.3 Step 3: Copy Eid Day Sales (CRITICAL)

#### The Rule
**Copy by EID DAY NUMBER, NOT by weekday!**

```
CY Eid Day 1 → BY Eid Day 1 (exact sales value, ignore weekday)
CY Eid Day 2 → BY Eid Day 2 (exact sales value, ignore weekday)
CY Eid Day 3 → BY Eid Day 3 (exact sales value, ignore weekday)
```

#### Example
```
CY 2025 Eid:
- Eid Day 1 (June 6, Friday): 5,000 BHD
- Eid Day 2 (June 7, Saturday): 6,000 BHD
- Eid Day 3 (June 8, Sunday): 4,500 BHD

BY 2026 Eid (weekdays are different):
- Eid Day 1 (May 27, Wednesday) → 5,000 BHD ✓
- Eid Day 2 (May 28, Thursday) → 6,000 BHD ✓
- Eid Day 3 (May 29, Friday) → 4,500 BHD ✓
```

#### Why This Approach?
1. **Cultural Pattern**: Eid Day 1 is always the main celebration (highest sales)
2. **Event Sequence**: Days 2 and 3 follow with their own patterns
3. **Not Weekday-Dependent**: Eid sales are driven by the celebration sequence, not which day of week it is
4. **Fixed 3-Day Event**: The pattern is Eid-specific, not weekday-specific

#### What NOT to Do
```
❌ WRONG: Match by weekday
CY June 6 (Friday): 5,000 BHD
BY May 29 (Friday) → 5,000 BHD  (This would be Eid Day 3, not Day 1!)

✓ CORRECT: Match by Eid day number
CY Eid Day 1: 5,000 BHD
BY Eid Day 1 → 5,000 BHD (regardless of weekday)
```

---

### 4.4 Step 4: Calculate Non-Eid Weekday Averages

#### For Each Affected Month in CY
1. **Identify non-Eid days** in that month
2. **Group by weekday** (Monday, Tuesday, etc.)
3. **Calculate average** for each weekday
4. **Use ONLY non-Eid days** for averaging

#### Example Calculation
```
CY June 2025 Non-Eid Days (27 days):

Mondays: June 2, 9, 16, 23, 30 (5 Mondays)
Sales: 3,100 + 3,000 + 2,900 + 3,050 + 3,200 = 15,250
Average: 15,250 / 5 = 3,050 BHD

Tuesdays: June 3, 10, 17, 24 (4 Tuesdays)
Sales: 2,800 + 2,900 + 2,750 + 2,850 = 11,300
Average: 11,300 / 4 = 2,825 BHD

... (continue for all weekdays, excluding Eid days)

Result:
- Monday avg: 3,050 BHD
- Tuesday avg: 2,825 BHD
- Wednesday avg: 2,900 BHD
- Thursday avg: 3,100 BHD
- Friday avg: 3,500 BHD (3 Fridays, excluding Eid Day 1)
- Saturday avg: 4,000 BHD (3 Saturdays, excluding Eid Day 2)
- Sunday avg: 3,200 BHD (3 Sundays, excluding Eid Day 3)
```

---

### 4.5 Step 5: Apply to BY Non-Eid Days

#### For Each Non-Eid Day in BY
1. **Determine the weekday** (e.g., Monday)
2. **Look up the weekday average** from corresponding CY month
3. **Assign that average** as the estimated sales

#### Example Application
```
BY May 2026 Non-Eid Days:

May 5 (Monday) → 3,050 BHD (from CY June Monday avg)
May 6 (Tuesday) → 2,825 BHD (from CY June Tuesday avg)
May 7 (Wednesday) → 2,900 BHD (from CY June Wednesday avg)
May 8 (Thursday) → 3,100 BHD (from CY June Thursday avg)
May 9 (Friday) → 3,500 BHD (from CY June Friday avg)
May 10 (Saturday) → 4,000 BHD (from CY June Saturday avg)
May 11 (Sunday) → 3,200 BHD (from CY June Sunday avg)
... (continue for all 28 non-Eid days)
```

---

### 4.6 Step 6: Calculate Month Impact

#### Formula
```
Month_CY_Total = Eid_Sales_CY + Non_Eid_Sales_CY
Month_BY_Estimated = Eid_Sales_BY + Non_Eid_Sales_BY

Impact_Percentage = ((Month_BY_Estimated - Month_CY_Total) / Month_CY_Total) × 100
```

#### Example
```
CY June 2025:
- Eid Sales: 15,500 BHD (3 days)
- Non-Eid Sales: 87,000 BHD (27 days)
- Total: 102,500 BHD

BY May 2026:
- Eid Sales: 15,500 BHD (exact copy)
- Non-Eid Sales: 89,000 BHD (estimated)
- Total: 104,500 BHD

Impact: (104,500 - 102,500) / 102,500 × 100 = +1.95%
```

---

### 4.7 CRITICAL RULE: Same Month Weekday Averages

**Each BY month ALWAYS uses its corresponding SAME month's CY non-Eid weekday averages.**

```
BY January → CY January non-Eid averages
BY February → CY February non-Eid averages
BY March → CY March non-Eid averages
...
BY December → CY December non-Eid averages
```

**Why This Works**:
- Each month has a minimum of **26 non-Eid days** (30-day month with 3 Eid days + 1 day buffer)
- 26 days is MORE than sufficient to calculate reliable weekday averages
- Each weekday will have 3-4 occurrences in the non-Eid days
- NO need to borrow averages from other months

**Example**:
```
June has 30 days total
- If 3 Eid days: 27 non-Eid days available ✓
- If Eid spans months (2 days): 28 non-Eid days available ✓
- Always enough data for reliable weekday averages

Weekday distribution in 27 non-Eid days:
- Monday: ~4 occurrences
- Tuesday: ~4 occurrences
- Wednesday: ~4 occurrences
- Thursday: ~4 occurrences
- Friday: ~3 occurrences
- Saturday: ~3 occurrences
- Sunday: ~3 occurrences
```

**NEVER cross-apply averages between months** - each month has its own seasonal/operational patterns.

---

## 5. IMPLEMENTATION REQUIREMENTS

### 5.1 Database Schema
```sql
-- Existing table (no changes needed)
TABLE: budget_runtime_state
- eid2_cy (Date, NOT NULL)
- eid2_by (Date, NOT NULL)
```

### 5.2 Backend Function Signature
```python
def Eid2Calculations(compare_year, eid2_CY, eid2_BY, df):
    """
    Calculate Eid Al-Adha impact based on month shift.
    
    Args:
        compare_year (int): Compare year (e.g., 2025)
        eid2_CY (datetime): CY Eid start date
        eid2_BY (datetime): BY Eid start date
        df (DataFrame): Historical sales data
    
    Returns:
        DataFrame with columns:
        - branch_id
        - month
        - actual (CY sales)
        - est (BY estimated sales)
        - Eid2 % (impact percentage)
    
    Special Cases:
        - If eid2_CY.month == eid2_BY.month: Return 0% impact
        - If Eid spans 2 months: Calculate each month separately
    """
```

### 5.3 Required Functions

#### Function 1: Check Same Month
```python
def check_same_month(eid2_CY, eid2_BY):
    """
    Check if Eid falls in same month in both years.
    
    Returns:
        bool: True if same month, False otherwise
    """
    cy_eid_end = eid2_CY + timedelta(days=2)
    by_eid_end = eid2_BY + timedelta(days=2)
    
    cy_months = set([eid2_CY.month, cy_eid_end.month])
    by_months = set([eid2_BY.month, by_eid_end.month])
    
    return cy_months == by_months
```

#### Function 2: Copy Eid Day Sales
```python
def copy_eid_day_sales(cy_eid_days_data, by_dates):
    """
    Copy CY Eid day sales to BY by Eid day number.
    
    Args:
        cy_eid_days_data: List of (date, sales) for CY Eid Days 1, 2, 3
        by_dates: List of BY dates for Eid Days 1, 2, 3
    
    Returns:
        dict: {by_date: cy_sales_value}
    
    Example:
        CY: [(2025-06-06, 5000), (2025-06-07, 6000), (2025-06-08, 4500)]
        BY: [2026-05-27, 2026-05-28, 2026-05-29]
        
        Result: {
            2026-05-27: 5000,  # Eid Day 1 → Day 1
            2026-05-28: 6000,  # Eid Day 2 → Day 2
            2026-05-29: 4500   # Eid Day 3 → Day 3
        }
    """
    result = {}
    for i, by_date in enumerate(by_dates):
        result[by_date] = cy_eid_days_data[i][1]  # Copy by position
    return result
```

#### Function 3: Calculate Non-Eid Weekday Averages
```python
def calculate_non_eid_weekday_avg(df, month, year, eid_dates):
    """
    Calculate weekday averages from non-Eid days only.
    
    Args:
        df: Sales dataframe
        month: Month number
        year: Year
        eid_dates: List of Eid dates to exclude
    
    Returns:
        dict: {weekday_name: average_sales}
    """
    # Filter to month and exclude Eid dates
    month_data = df[(df['date'].dt.month == month) & 
                    (df['date'].dt.year == year) &
                    (~df['date'].isin(eid_dates))]
    
    # Group by weekday and calculate average
    weekday_avg = month_data.groupby(
        month_data['date'].dt.day_name()
    )['gross'].mean().to_dict()
    
    return weekday_avg
```

### 5.4 Output Format

#### When Same Month
```json
{
  "branch_id": 189,
  "affected_months": [6],
  "message": "Eid Al-Adha falls in the same month in both years",
  "impact": 0,
  "months": [
    {
      "month": 6,
      "actual": 0,
      "est": 0,
      "Eid2 %": 0
    }
  ]
}
```

#### When Different Month
```json
{
  "branch_id": 189,
  "affected_months": [5, 6],
  "cy_eid_month": 6,
  "by_eid_month": 5,
  "months": [
    {
      "month": 5,
      "actual": 0,
      "est": 104500,
      "Eid2 %": "+inf",
      "details": {
        "eid_sales": 15500,
        "non_eid_sales": 89000
      }
    },
    {
      "month": 6,
      "actual": 102500,
      "est": 0,
      "Eid2 %": "-100",
      "details": {
        "eid_sales": 15500,
        "non_eid_sales": 87000
      }
    }
  ]
}
```

---

## 6. EXAMPLES

### Example 1: Same Month (No Impact)

**Input**:
```
eid2_CY: 2025-06-15
eid2_BY: 2026-06-04
```

**Analysis**:
```
CY Eid: June 15, 16, 17 (Month: 6)
BY Eid: June 4, 5, 6 (Month: 6)

Month check: 6 == 6 (Same month)
```

**Output**:
```
Impact: 0%
Message: "Eid Al-Adha falls in the same month in both years - No sales effect"
```

---

### Example 2: Different Month, Single Month Each

**Input**:
```
eid2_CY: 2025-06-06
eid2_BY: 2026-05-27
```

**Analysis**:
```
CY Eid: June 6, 7, 8 (Month: 6)
BY Eid: May 27, 28, 29 (Month: 5)

Month check: 6 != 5 (Different months)
Eid within one month for both years
```

**CY June 2025**:
```
Total Days: 30
- Eid Days (3): June 6, 7, 8
  - Eid Day 1: 5,000 BHD
  - Eid Day 2: 6,000 BHD
  - Eid Day 3: 4,500 BHD
  - Subtotal: 15,500 BHD

- Non-Eid Days (27): June 1-5, 9-30
  - Weekday averages calculated
  - Subtotal: 87,000 BHD

Total: 102,500 BHD
```

**BY May 2026**:
```
Total Days: 31
- Eid Days (3): May 27, 28, 29
  - Eid Day 1: 5,000 BHD (copy from CY Day 1)
  - Eid Day 2: 6,000 BHD (copy from CY Day 2)
  - Eid Day 3: 4,500 BHD (copy from CY Day 3)
  - Subtotal: 15,500 BHD

- Non-Eid Days (28): May 1-26, 30-31
  - Apply CY June weekday averages
  - Subtotal: 89,000 BHD

Total: 104,500 BHD
```

**Output**:
```
June Impact: (0 - 102,500) / 102,500 × 100 = -100%
May Impact: (104,500 - 0) / 0 → +inf (new Eid month)

Overall: Eid shifted from June to May
```

---

### Example 3: Eid Spans Two Months

**Input**:
```
eid2_CY: 2025-06-29
eid2_BY: 2026-05-30
```

**Analysis**:
```
CY Eid: June 29, 30 + July 1 (Months: 6, 7)
BY Eid: May 30, 31 + June 1 (Months: 5, 6)

Month check: {6, 7} != {5, 6} (Different months)
Eid spans two months in both years
```

**CY June 2025**:
```
- Eid Days: June 29, 30 (2 days)
  - Eid Day 1: 5,000 BHD
  - Eid Day 2: 6,000 BHD
  - Subtotal: 11,000 BHD

- Non-Eid Days: June 1-28 (28 days)
  - Calculate weekday averages
  - Subtotal: 85,000 BHD

Total: 96,000 BHD
```

**CY July 2025**:
```
- Eid Days: July 1 (1 day)
  - Eid Day 3: 4,500 BHD
  - Subtotal: 4,500 BHD

- Non-Eid Days: July 2-31 (30 days)
  - Calculate weekday averages
  - Subtotal: 90,000 BHD

Total: 94,500 BHD
```

**BY May 2026**:
```
- Eid Days: May 30, 31 (2 days)
  - Eid Day 1: 5,000 BHD (from CY Day 1)
  - Eid Day 2: 6,000 BHD (from CY Day 2)
  - Subtotal: 11,000 BHD

- Non-Eid Days: May 1-29 (29 days)
  - Apply CY MAY weekday averages (29 non-Eid days available)
  - Subtotal: 87,500 BHD

Total: 98,500 BHD
```

**BY June 2026**:
```
- Eid Days: June 1 (1 day)
  - Eid Day 3: 4,500 BHD (from CY Day 3)
  - Subtotal: 4,500 BHD

- Non-Eid Days: June 2-30 (29 days)
  - Apply CY JUNE weekday averages (28 non-Eid days available in CY June)
  - Subtotal: 87,000 BHD

Total: 91,500 BHD
```

**Output**:
```
CY June (96,000) → BY May (98,500): +2.60%
CY July (94,500) → BY June (91,500): -3.17%

Four months affected: June/July (CY), May/June (BY)
```

---

## 7. COMPARISON WITH OTHER ISLAMIC EVENTS

### 7.1 Overview Table

| Feature | Ramadan | Muharram | Eid Al-Adha |
|---------|---------|----------|-------------|
| **Duration** | ~30 days | ~30 days | **3 days** |
| **Type** | Period | Period | **Event** |
| **Database Fields** | Date + daycount (2 fields per year) | Date + daycount (2 fields per year) | **Date only (1 field per year)** |
| **Same Month Logic** | ALWAYS calculate | ALWAYS calculate | **NO calculation if same month** |
| **Day Matching** | Weekday matching | Weekday matching | **Eid day number matching** |
| **Weekday Averages** | Complex (Ramadan vs Non-Ramadan) | Two-tier (Muharram vs Non-Muharram) | **Simple (Non-Eid only)** |
| **Complexity** | HIGH | HIGH | **MEDIUM** |

### 7.2 Detailed Comparison

#### Ramadan
- **What**: 30-day fasting period
- **Impact**: Sales patterns change during fasting (lower daytime, higher evening)
- **Calculation**: Weekday averaging for both Ramadan and non-Ramadan days
- **Same Month**: Always calculates (even if Ramadan stays in March both years)

#### Muharram
- **What**: 30-day mourning period (first month of Islamic calendar)
- **Impact**: Lower sales during mourning period
- **Calculation**: TWO separate weekday averages (NON-MUHARRAM vs MUHARRAM)
- **Same Month**: Always calculates (period shift within months matters)

#### Eid Al-Adha
- **What**: 3-day celebration
- **Impact**: High sales spike during celebration days
- **Calculation**: Direct copy of Eid day sales + weekday averaging for non-Eid days
- **Same Month**: NO calculation if Eid stays in same month (no shift = no impact)

### 7.3 Why Eid Al-Adha is Different

1. **Short Event**: Only 3 days vs 30 days
2. **Month Shift Focus**: Only matters if Eid moves to different month
3. **Cultural Pattern**: Eid Day 1, 2, 3 have fixed cultural significance
4. **No Weekday Dependency**: Eid celebration pattern is independent of weekday
5. **Simpler Logic**: Binary decision (same month vs different month)

---

## 8. VALIDATION & TESTING

### 8.1 Test Cases

#### Test Case 1: Same Month
```
Input:
- eid2_CY: 2025-06-15
- eid2_BY: 2026-06-08

Expected Output:
- Impact: 0%
- Message: "Eid falls in same month - No sales effect"
- No calculation performed
```

#### Test Case 2: Month Shift Within One Month
```
Input:
- eid2_CY: 2025-06-06
- eid2_BY: 2026-05-27
- CY June Eid sales: [5000, 6000, 4500]
- CY June non-Eid weekday avgs: {...}

Expected Output:
- May impact: +inf (gained Eid)
- June impact: -100% (lost Eid)
- BY May Eid days: [5000, 6000, 4500] (exact copy)
```

#### Test Case 3: Month Shift Spanning Two Months
```
Input:
- eid2_CY: 2025-06-29
- eid2_BY: 2026-05-30

Expected Output:
- 4 months affected: June/July (CY), May/June (BY)
- Each month calculated separately
- Eid days copied by day number
- Non-Eid days use corresponding CY month averages
```

### 8.2 Edge Cases

#### Edge Case 1: Eid on Month Boundary
```
Scenario: Eid starts on last day of month
- eid2_CY: 2025-06-30

Handling:
- June: 1 Eid day (Day 1)
- July: 2 Eid days (Days 2, 3)
- Calculate each month separately
```

#### Edge Case 2: Leap Year
```
Scenario: Eid in February during leap year

Handling:
- Account for Feb 29 in leap years
- Adjust non-Eid day counts accordingly
```

#### Edge Case 3: No Historical Data
```
Scenario: Branch has no CY data for Eid month

Handling:
- Skip that branch
- Return empty result or use fallback logic
- Log warning for missing data
```

---

## 9. IMPLEMENTATION CHECKLIST

### Phase 1: Detection Logic
- [ ] Implement same month detection function
- [ ] Test with various date combinations
- [ ] Verify correct "no impact" message display

### Phase 2: Eid Day Copying
- [ ] Implement Eid day number matching (NOT weekday)
- [ ] Verify Day 1 → Day 1, Day 2 → Day 2, Day 3 → Day 3
- [ ] Test with different weekday combinations

### Phase 3: Non-Eid Averaging
- [ ] Calculate weekday averages from non-Eid days only
- [ ] Handle single month vs two-month spanning
- [ ] Match CY month averages to correct BY month

### Phase 4: Impact Calculation
- [ ] Calculate month totals (Eid + Non-Eid)
- [ ] Compute impact percentages
- [ ] Handle edge cases (divide by zero, etc.)

### Phase 5: Testing
- [ ] Test all test cases listed above
- [ ] Validate with real historical data
- [ ] Compare with manual calculations

### Phase 6: Documentation
- [ ] Update API documentation
- [ ] Create user guide
- [ ] Add inline code comments

---

## 10. CONCLUSION

This specification defines the complete business logic for Eid Al-Adha calculation in the Budget Management System.

**Key Takeaways**:
1. **Month shift is the trigger**: Same month = no calculation
2. **Eid days copy by number**: Day 1 → Day 1, not by weekday
3. **Non-Eid days use weekday averages**: Calculated per month separately
4. **Simpler than Ramadan/Muharram**: Binary logic, fixed 3-day event

**Ready for Implementation**: This document provides all necessary details for development team to implement the Eid Al-Adha calculation system.

---

**Document Status**: ✅ APPROVED  
**Last Updated**: November 26, 2025  
**Next Review**: Before implementation begins

---
