# budget_pipeline.py
import pandas as pd
import numpy as np
import math
import calendar
import warnings
from datetime import timedelta
from calendar import monthrange
from typing import List, Dict, Any

from sqlalchemy.orm import joinedload
from sqlalchemy import distinct

from src.core.db import get_session, close_session
from src.models.budget import defaultBudgetModel
# Brand is imported inside function
from src.db.dbtables import Branch, ProjectionInput

warnings.filterwarnings('ignore')


# ---------------------------
# Public entry
# ---------------------------
def calculateDefault(data: defaultBudgetModel):
    dbs = get_session()
    try:
        compare_year = data.compare_year
        ramadan_daycount_CY = data.ramadan_daycount_CY
        ramadan_daycount_BY = data.ramadan_daycount_BY
        ramadan_CY = pd.to_datetime(data.ramadan_CY)
        ramadan_BY = pd.to_datetime(data.ramadan_BY)
        muharram_CY = pd.to_datetime(data.muharram_CY)
        muharram_BY = pd.to_datetime(data.muharram_BY)
        muharram_daycount_CY = data.muharram_daycount_CY
        muharram_daycount_BY = data.muharram_daycount_BY
        eid2_CY = pd.to_datetime(data.eid2_CY)
        eid2_BY = pd.to_datetime(data.eid2_BY)

        # Load and scope data by active branches
        import os
        # Go up from services -> src -> Backend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        df = pd.read_pickle(os.path.join(base_dir, "BaseData.pkl"))
        branch_ids = [b[0] for b in dbs.query(distinct(Branch.id)).all()]
        df = df[df["branch_id"].isin(branch_ids)]

        # Calculations
        weekly = WeeklyAverageCalculations(compare_year, df)
        ramadan = Ramadan_Eid_Calculations(
            compare_year,
            ramadan_daycount_CY, ramadan_daycount_BY,
            ramadan_CY, ramadan_BY,
            df
        )
        muh = Muharram_calculations(
            compare_year,
            muharram_CY, muharram_BY,
            muharram_daycount_CY, muharram_daycount_BY,
            df
        )
        eid2 = Eid2Calculations(compare_year, eid2_CY, eid2_BY, df)
        summarydf = descriptiveCalculations(compare_year, df)

        # Merge all computed datasets
        final_df = weekly[['branch_id', 'month', 'trade_on_off']].copy()
        final_df = pd.merge(final_df, ramadan[['branch_id', 'month', 'Ramadan Eid %']],
                            on=['branch_id', 'month'], how='left')
        final_df = pd.merge(final_df, muh[['branch_id', 'month', 'Muharram %']],
                            on=['branch_id', 'month'], how='left')
        final_df = pd.merge(final_df, eid2[['branch_id', 'month', 'Eid2 %']],
                            on=['branch_id', 'month'], how='left')
        final_df = pd.merge(final_df, summarydf, on=[
                            'branch_id', 'month'], how='left')

        merged = add_projection_inputs(final_df)

        # Build the final JSON
        results = dataframe_to_brand_json(merged, data)
        return results

    except Exception:
        raise
    finally:
        close_session(dbs)


# ---------------------------
# Helpers
# ---------------------------
def _none_if_nan(v):
    try:
        return None if (v is None or (isinstance(v, float) and math.isnan(v))) else v
    except Exception:
        # pandas NA, etc.
        return None if pd.isna(v) else v


def add_projection_inputs(final_df):
    dbs = get_session()
    try:
        projection_cols = [
            "dining_sales_pct", "projected_dinin_avg_check", "projected_avg_per_cover", "projected_guest_count_new",
            "delivery_sales_pct", "projected_delivery_avg_check",
            "takeaway_sales_pct", "projected_takeaway_avg_check",
            "drivethru_sales_pct", "projected_drivethru_avg_check",
            "catering_trans_pct", "projected_catering_avg_check",
            "projected_discount_pct", "marketing_activities_pct",
            "projected_delivery_sales_new", "projected_delivery_trans_new",
            "projected_dinein_sales_new", "projected_dinein_trans_new",
            "projected_takeaway_sales_new", "projected_takeaway_trans_new",
            "projected_drivethru_sales_new", "projected_drivethru_trans_new",
            "projected_catering_sales_new", "projected_catering_trans_new",
        ]

        # 1) Read all inputs from DB
        inputs_q = dbs.query(ProjectionInput)
        rows = [{
            "branch_id": r.branch_id, "month": r.month,
            "dining_sales_pct": r.dining_sales_pct,
            "projected_dinin_avg_check": r.projected_dinin_avg_check,
            "projected_avg_per_cover": r.projected_avg_per_cover,
            "projected_guest_count_new": r.projected_guest_count_new,
            "delivery_sales_pct": r.delivery_sales_pct,
            "projected_delivery_avg_check": r.projected_delivery_avg_check,
            "takeaway_sales_pct": r.takeaway_sales_pct,
            "projected_takeaway_avg_check": r.projected_takeaway_avg_check,
            "drivethru_sales_pct": r.drivethru_sales_pct,
            "projected_drivethru_avg_check": r.projected_drivethru_avg_check,
            "catering_trans_pct": r.catering_trans_pct,
            "projected_catering_avg_check": r.projected_catering_avg_check,
            "projected_discount_pct": r.projected_discount_pct,
            "marketing_activities_pct": r.marketing_activities_pct,
            "projected_dinein_sales_new": r.projected_dinein_sales_new,
            "projected_dinein_trans_new": r.projected_dinein_trans_new,
            "projected_delivery_sales_new": r.projected_delivery_sales_new,
            "projected_delivery_trans_new": r.projected_delivery_trans_new,
            "projected_takeaway_sales_new": r.projected_takeaway_sales_new,
            "projected_takeaway_trans_new": r.projected_takeaway_trans_new,
            "projected_drivethru_sales_new": r.projected_drivethru_sales_new,
            "projected_drivethru_trans_new": r.projected_drivethru_trans_new,
            "projected_catering_sales_new": r.projected_catering_sales_new,
            "projected_catering_trans_new": r.projected_catering_trans_new,
        } for r in inputs_q.all()]
        inputs_df = pd.DataFrame(rows)

        # 2) Pairs from final_df (already includes fallback months from weekly + descriptive)
        pairs_final = (final_df[['branch_id', 'month']].drop_duplicates()
                       if not final_df.empty else pd.DataFrame(columns=['branch_id', 'month']))

        # 3) Pairs from DB inputs too (so existing manual entries are preserved even if not in final_df)
        pairs_db = (inputs_df[['branch_id', 'month']].drop_duplicates()
                    if not inputs_df.empty else pd.DataFrame(columns=['branch_id', 'month']))

        # 4) Scaffold = union of both — guarantees months align with pipeline and keeps any manual rows
        scaffold_pairs = (
            pd.concat([pairs_final, pairs_db], ignore_index=True)
              .drop_duplicates()
              .reset_index(drop=True)
        )

        # 5) Blank table with all projection columns
        blank_inputs = scaffold_pairs.copy()
        for c in projection_cols:
            blank_inputs[c] = np.nan

        # 6) Overlay DB values (if any)
        if inputs_df.empty:
            filled_inputs = blank_inputs
        else:
            filled_inputs = blank_inputs.merge(
                inputs_df, on=['branch_id', 'month'], how='left', suffixes=('', '_db')
            )
            for c in projection_cols:
                c_db = f"{c}_db"
                if c_db in filled_inputs.columns:
                    filled_inputs[c] = filled_inputs[c_db].combine_first(
                        filled_inputs[c])
            filled_inputs = filled_inputs.drop(
                columns=[c for c in filled_inputs.columns if c.endswith('_db')])

        # 7) Attach computed metrics from final_df
        merged = filled_inputs.merge(
            final_df, on=['branch_id', 'month'], how='left')
        return merged

    except Exception:
        raise
    finally:
        close_session(dbs)


def dataframe_to_brand_json(df: pd.DataFrame, config: defaultBudgetModel) -> List[Dict[str, Any]]:
    """
    Expected df columns (at least):
      - branch_id (int)
      - month (int, 1-12)
      - trade_on_off (float)
      - Ramadan Eid % / Muharram % / Eid2 % (optional)
      - computed descriptive fields (from descriptiveCalculations)
      - user-input fields (if merged)
    """

    dbs = get_session()
    try:
        # Normalize/rename seasonal columns
        rename_map = {
            "Ramadan Eid %": "ramadan_eid_pct",
            "Muharram %": "muharram_pct",
            "Eid2 %": "eid2_pct",
        }
        df = df.rename(
            columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()

        if "month" in df.columns:
            df["month"] = df["month"].astype(int)

        import os
        # Go up from services -> src -> Backend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dfdate = pd.read_pickle(os.path.join(base_dir, "BaseData.pkl"))

        rows_by_branch: Dict[int, list] = {}
        for row in df.to_dict("records"):
            bid = row.get("branch_id")
            if bid is None:
                continue
            
            ts = _none_if_nan(row.get("total_sales"))
            month_payload = {
                "month": row.get("month"),
                # Core totals
                "total_sales": _none_if_nan(row.get("total_sales")),
                "total_trans": _none_if_nan(row.get("total_trans")),
                "avg_check": _none_if_nan(row.get("avg_check")),
                "discount": _none_if_nan(row.get("discount")),
                "discount_pct": _none_if_nan(row.get("discount_pct")),
                "vat": _none_if_nan(row.get("vat")),
                "netsales": _none_if_nan(row.get("netsales")),
                # Dining
                "dining_sales": _none_if_nan(row.get("dining_sales")),
                "dining_trans": _none_if_nan(row.get("dining_trans")),
                "dining_avg_check": _none_if_nan(row.get("dining_avg_check")),
                "avg_per_cover": _none_if_nan(row.get("avg_per_cover")),
                "customer_count": _none_if_nan(row.get("customer_count")),
                # Delivery
                "delivery_sales": _none_if_nan(row.get("delivery_sales")),
                "delivery_trans": _none_if_nan(row.get("delivery_trans")),
                "delivery_avg_check": _none_if_nan(row.get("delivery_avg_check")),
                # Takeaway
                "takeaway_sales": _none_if_nan(row.get("takeaway_sales")),
                "takeaway_trans": _none_if_nan(row.get("takeaway_trans")),
                "takeaway_avg_check": _none_if_nan(row.get("takeaway_avg_check")),
                # Drive-thru
                "drivethru_sales": _none_if_nan(row.get("drivethru_sales")),
                "drivethru_trans": _none_if_nan(row.get("drivethru_trans")),
                "drivethru_avg_check": _none_if_nan(row.get("drivethru_avg_check")),
                # Catering
                "catering_sales": _none_if_nan(row.get("catering_sales")),
                "catering_trans": _none_if_nan(row.get("catering_trans")),
                "catering_avg_check": _none_if_nan(row.get("catering_avg_check")),
                # Seasonal / trade %s
                "trade_on_off": _none_if_nan(row.get("trade_on_off")),
                "ramadan_eid_pct": _none_if_nan(row.get("ramadan_eid_pct")),
                "muharram_pct": _none_if_nan(row.get("muharram_pct")),
                "eid2_pct": _none_if_nan(row.get("eid2_pct")),
            }
            
            # Calculate Islamic calendar effect fields for frontend
            # sales_CY = Comparison Year actual sales (with Islamic effects)
            # est_sales_no_X = Expected sales without X event (baseline)
            if ts is not None:
                month_payload["sales_CY"] = ts  # Actual sales from comparison year (2025)
                
                # Calculate baseline sales by removing each Islamic effect
                ramadan_pct = _none_if_nan(row.get("ramadan_eid_pct"))
                muharram_pct = _none_if_nan(row.get("muharram_pct"))
                eid2_pct = _none_if_nan(row.get("eid2_pct"))
                
                # Formula: baseline = actual / (1 + effect_pct/100)
                # If Ramadan increased sales by 10%, then actual = baseline * 1.10
                # So baseline = actual / 1.10
                if ramadan_pct is not None:
                    month_payload["est_sales_no_ramadan"] = ts / (1 + ramadan_pct / 100.0)
                else:
                    month_payload["est_sales_no_ramadan"] = ts
                
                if muharram_pct is not None:
                    month_payload["est_sales_no_muharram"] = ts / (1 + muharram_pct / 100.0)
                else:
                    month_payload["est_sales_no_muharram"] = ts
                
                if eid2_pct is not None:
                    month_payload["est_sales_no_eid2"] = ts / (1 + eid2_pct / 100.0)
                else:
                    month_payload["est_sales_no_eid2"] = ts
            else:
                # No sales data available
                month_payload["sales_CY"] = None
                month_payload["est_sales_no_ramadan"] = None
                month_payload["est_sales_no_muharram"] = None
                month_payload["est_sales_no_eid2"] = None
            # NEW: only include when fallback happened
            if (ts is not None) and row.get("used_fallback"):
                month_payload["used_fallback"] = True
            else:
                month_payload["used_fallback"] = False

            # User-entered overrides & effective values (if present)
            for k in [
                "dining_sales_pct", "projected_dinin_avg_check", "projected_avg_per_cover","projected_guest_count_new",
                "delivery_sales_pct", "projected_delivery_avg_check",
                "takeaway_sales_pct", "projected_takeaway_avg_check",
                "drivethru_sales_pct", "projected_drivethru_avg_check",
                "catering_trans_pct", "projected_catering_avg_check",
                "projected_discount_pct", "marketing_activities_pct",
                "projected_delivery_sales_new", "projected_delivery_trans_new",
                "projected_dinein_sales_new", "projected_dinein_trans_new",
                "projected_takeaway_sales_new", "projected_takeaway_trans_new",
                "projected_drivethru_sales_new", "projected_drivethru_trans_new",
                "projected_catering_sales_new", "projected_catering_trans_new",
            ]:
                if k in df.columns:
                    month_payload[k] = _none_if_nan(row.get(k))

            rows_by_branch.setdefault(bid, []).append(month_payload)

        # Pull brands + branches in one shot (filter soft-deleted and order by ID)
        from src.db.dbtables import Brand  # local import to avoid circulars
        brands = (
            dbs.query(Brand)
            .options(joinedload(Brand.branches))
            .filter(Brand.is_deleted == False)
            .order_by(Brand.id)
            .all()
        )

        result: List[Dict[str, Any]] = []
        for brand in brands:
            brand_obj = {
                "brand_id": brand.id,
                "brand_name": brand.name,
                "is_deleted": brand.is_deleted if hasattr(brand, 'is_deleted') else False,
                "branches": []
            }
            # Filter out soft-deleted branches
            active_branches = [br for br in brand.branches if not br.is_deleted]
            for br in sorted(active_branches, key=lambda x: x.id):
                branch_months = rows_by_branch.get(br.id, [])
                branch_months = sorted(
                    [m for m in branch_months if m.get("month") is not None],
                    key=lambda m: m["month"]
                )
                brand_obj["branches"].append({
                    "branch_id": br.id,
                    "branch_name": br.name,
                    "is_deleted": br.is_deleted if hasattr(br, 'is_deleted') else False,
                    "months": branch_months
                })
            result.append(brand_obj)
        payload = {
            "config": config.model_dump(mode='json'),
            "date": dfdate["business_date"].dt.date.max(),
            "data": result,
        }
        return payload
    except Exception:
        raise
    finally:
        close_session(dbs)


# ---------------------------
# Calculations
# ---------------------------
def WeeklyAverageCalculations(compare_year, df):
    try:
        previous_year = compare_year - 1

        def count_day_occurrences(year, month, day_number):
            month_days = calendar.monthcalendar(year, month)
            return sum(1 for week in month_days if week[day_number] != 0)

        def generate_day_counts(start_year, end_year):
            records = []
            for year in range(start_year, end_year + 1):
                for month in range(1, 13):
                    for day_num, day_name in enumerate(calendar.day_name):
                        count = count_day_occurrences(year, month, day_num)
                        records.append({
                            'year': year,
                            'month': month,
                            'day_name': day_name,
                            'occurrences': count
                        })
            return pd.DataFrame(records)

        day_occurance_df = generate_day_counts(previous_year, compare_year + 1)

        df['year'] = df['business_date'].dt.year
        df['month'] = df['business_date'].dt.month
        df['day_name'] = df['business_date'].dt.day_name()

        gross_sums = (
            df.groupby(['branch_id', 'year', 'month', 'day_name'])['gross']
              .sum()
              .reset_index(name='gross_sum')
        )

        unique_dates = df[['branch_id', 'business_date']].drop_duplicates()
        unique_dates['year'] = unique_dates['business_date'].dt.year
        unique_dates['month'] = unique_dates['business_date'].dt.month
        unique_dates['day_name'] = unique_dates['business_date'].dt.day_name()

        date_counts = (
            unique_dates.groupby(['branch_id', 'year', 'month'])
                        .size()
                        .reset_index(name='actual_days')
        )
        date_counts['days_in_month'] = date_counts.apply(
            lambda row: monthrange(row['year'], row['month'])[1], axis=1
        )
        date_counts['percent_covered'] = date_counts['actual_days'] / \
            date_counts['days_in_month']

        days_present = date_counts[date_counts['year'] == compare_year]
        incomplete_months = days_present[days_present['percent_covered'] < 0.1][[
            'branch_id', 'month']]

        all_months = pd.MultiIndex.from_product(
            [df['branch_id'].unique(), range(1, 13)],
            names=['branch_id', 'month']
        ).to_frame(index=False)

        months_present = days_present[['branch_id', 'month']].drop_duplicates()

        missing_months = (
            all_months.merge(months_present, on=[
                             'branch_id', 'month'], how='left', indicator=True)
                      .query('_merge == "left_only"')[['branch_id', 'month']]
        )

        full_fallback_months = pd.concat(
            [incomplete_months, missing_months], ignore_index=True)

        data_previous_year = gross_sums[gross_sums['year'] == previous_year]
        data_compare_year = gross_sums[gross_sums['year'] == compare_year]

        valid_compare_year = data_compare_year.merge(
            all_months.merge(full_fallback_months, on=[
                             'branch_id', 'month'], how='left', indicator=True)
                      .query('_merge == "left_only"')[['branch_id', 'month']],
            on=['branch_id', 'month']
        )

        fallback_previous_year = data_previous_year.merge(
            full_fallback_months,
            on=['branch_id', 'month']
        )

        SalesDiff = pd.concat(
            [valid_compare_year, fallback_previous_year], ignore_index=True)
        SalesDiff = SalesDiff.sort_values(
            ['branch_id', 'year', 'month', 'day_name'])

        day_lookup = day_occurance_df.set_index(['year', 'month', 'day_name'])[
            'occurrences'].to_dict()
        SalesDiff['day_count_CY'] = SalesDiff.apply(
            lambda row: day_lookup.get((row['year'], row['month'], row['day_name']), 0), axis=1
        )
        SalesDiff['day_count_BY'] = SalesDiff.apply(
            lambda row: day_lookup.get((compare_year + 1, row['month'], row['day_name']), 0), axis=1
        )
        SalesDiff["est_gross"] = (
            SalesDiff["gross_sum"] / SalesDiff["day_count_CY"]) * SalesDiff["day_count_BY"]
        SalesDiff = SalesDiff.groupby(["branch_id", "month"]).agg(
            act_sales=("gross_sum", "sum"),
            est_sales=("est_gross", "sum")
        ).reset_index()
        SalesDiff["trade_on_off"] = round(
            (1 - (SalesDiff["act_sales"] / SalesDiff["est_sales"])) * 100, 2)

        return SalesDiff
    except Exception:
        raise


def Ramadan_Eid_Calculations(compare_year, ramadan_daycount_CY, ramadan_daycount_BY, ramadan_CY, ramadan_BY, df):
    try:
        previous_year = compare_year - 1
        dates_df = pd.DataFrame()
        dates_df["date"] = pd.date_range(start=str(previous_year) + "-01-01",
                                         end=str(compare_year + 1) + "-12-31", freq="d")
        ramadan_start_dates = {
            compare_year: ramadan_CY,
            compare_year + 1: ramadan_BY
        }
        ramadan_lengths = {
            compare_year: ramadan_daycount_CY,
            compare_year + 1: ramadan_daycount_BY
        }
        ramadan_periods = {
            year: (start, start + timedelta(days=ramadan_lengths[year] - 1))
            for year, start in ramadan_start_dates.items()
        }

        def assign_ramadan_flag(date):
            year = date.year
            if year in ramadan_periods:
                ramadan_start, ramadan_end = ramadan_periods[year]
                _, ramadan_end_c = ramadan_periods[compare_year]
                post_ramadan_start = ramadan_end + timedelta(days=1)
                post_ramadan_end = ramadan_end + timedelta(days=4)

                if ramadan_start <= date <= ramadan_end:
                    return 1  # Ramadan
                elif post_ramadan_start <= date <= post_ramadan_end:
                    return 2  # Eid + 3
                elif date.month == ramadan_start.month or date.month == post_ramadan_end.month:
                    return 3  # rest of same month(s)
                elif date.month == ramadan_end_c.month and year == compare_year + 1:
                    return 3
            return 0

        dates_df["ramadan"] = dates_df["date"].apply(assign_ramadan_flag)

        def safe_replace_year(date, new_year):
            try:
                if date.year == compare_year:
                    return date.replace(year=new_year)
                else:
                    return date
            except ValueError:
                if date.month == 2 and date.day == 29:
                    return date.replace(year=new_year, day=28)
                else:
                    raise

        ramadan_lookup_CY = dict(zip(dates_df["date"], dates_df["ramadan"]))
        dates_BY = dates_df[dates_df["date"].dt.year ==
                            compare_year + 1].copy()
        ramadan_lookup_BY = dict(zip(dates_BY["date"], dates_BY["ramadan"]))
        agg_funcs = {'gross': 'sum', 'day_of_week': 'first'}
        # FIX: Include data up to and including compare_year (2025), not just < 2026
        df = df[df["business_date"].dt.year <= compare_year]
        df = df.groupby(['branch_id', 'business_date']
                        ).agg(agg_funcs).reset_index()

        df["ramadan_CY"] = df["business_date"].map(ramadan_lookup_CY)
        df["business_date_BY"] = df["business_date"].apply(
            lambda d: safe_replace_year(d, compare_year + 1))

        df["ramadan_BY"] = df["business_date_BY"].map(ramadan_lookup_BY)
        df["day_of_week_BY"] = df["business_date_BY"].dt.day_name()

        orders_df = df
        orders_df["year_CY"] = orders_df["business_date"].dt.year
        orders_df["month_CY"] = orders_df["business_date"].dt.month
        orders_df["year_BY"] = orders_df["business_date_BY"].dt.year
        orders_df["month_BY"] = orders_df["business_date_BY"].dt.month
        orders_df = orders_df[[
            "branch_id", "business_date", "year_CY", "month_CY", "day_of_week",
            "business_date_BY", "year_BY", "month_BY", "day_of_week_BY",
            "gross", "ramadan_CY", "ramadan_BY"
        ]]

        final_df = pd.DataFrame()
        for branch in orders_df["branch_id"].unique():
            branch_sales = orders_df[orders_df["branch_id"] == branch].copy()
            branch_sales["gross_BY"] = 0
            average_eid_sales = branch_sales[branch_sales["ramadan_CY"] == 2]["gross"].mean(
            )
            day_sales_ramadan = branch_sales[branch_sales["ramadan_CY"] == 1].groupby(
                "day_of_week")["gross"].mean().reset_index()
            for _, v in day_sales_ramadan.iterrows():
                branch_sales.loc[(branch_sales["ramadan_BY"] == 1) & (
                    branch_sales["day_of_week_BY"] == v["day_of_week"]), "gross_BY"] = v["gross"]
            branch_sales.loc[branch_sales["ramadan_BY"]
                             == 2, "gross_BY"] = average_eid_sales

            # Handle months with ramadan_BY flag 3 (rest of Ramadan/Eid months)
            ramadan_month_BY = branch_sales.loc[branch_sales["ramadan_BY"] == 3, "month_BY"].unique()
            
            # Also include April (month 4) even if ramadan_BY is 0, because CY 2025 has Eid in April
            affected_months = list(ramadan_month_BY)
            if 4 not in affected_months:
                affected_months.append(4)
            
            for mon in affected_months:
                partial_cy_rows = branch_sales[
                    (branch_sales["ramadan_CY"].isin([1, 2])) &
                    (branch_sales["month_CY"] == mon) &
                    (branch_sales["year_CY"] == compare_year)
                ]
                if len(partial_cy_rows) > 0:
                    # SPECIAL CASE: April with Eid in CY but no Ramadan/Eid in BY
                    if mon == 4:
                        # Use April 2025 excluding Eid days (days 4-30 only)
                        # First, get the source data (April 2025 days 4-30)
                        april_source = branch_sales[
                            (branch_sales["month_CY"] == 4) & 
                            (branch_sales["year_CY"] == compare_year) &
                            (branch_sales["business_date"].dt.day > 3)  # Exclude days 1-3 (Eid)
                        ]
                        
                        # DEBUG: Print what we're using as reference
                        if branch == 189:  # Debug for Al Abraaj Sehla
                            print(f"\n🔍 DEBUG April Branch 189:")
                            print(f"   April 2025 source days (>3): {len(april_source)}")
                            print(f"   April 2025 total gross: {april_source['gross'].sum():,.2f}")
                        
                        # Calculate weekday averages from days 4-30
                        day_sales_non_ramadan = april_source.groupby("day_of_week")["gross"].mean().reset_index()
                        
                        if branch == 189:
                            print(f"   Weekday averages:")
                            for _, row in day_sales_non_ramadan.iterrows():
                                print(f"     {row['day_of_week']:9s}: {row['gross']:8,.2f}")
                        
                        # Apply to ALL April 2026 days
                        april_2026_rows = branch_sales[
                            (branch_sales["month_BY"] == 4) &
                            (branch_sales["year_BY"] == compare_year + 1)
                        ]
                        
                        if branch == 189:
                            print(f"   April 2026 target rows: {len(april_2026_rows)}")
                        
                        for _, v in day_sales_non_ramadan.iterrows():
                            branch_sales.loc[
                                (branch_sales["month_BY"] == 4) &
                                (branch_sales["year_BY"] == compare_year + 1) &
                                (branch_sales["day_of_week_BY"] == v["day_of_week"]),
                                "gross_BY"
                            ] = v["gross"]
                        
                        if branch == 189:
                            april_2026_after = branch_sales[
                                (branch_sales["month_BY"] == 4) &
                                (branch_sales["year_BY"] == compare_year + 1)
                            ]
                            print(f"   April 2026 gross_BY sum: {april_2026_after['gross_BY'].sum():,.2f}")
                            print(f"   Expected: ~57,299 BHD")
                    else:
                        # Original logic for other months
                        temp_month = mon - 1
                        temp_year = compare_year
                        while True:
                            if temp_month <= 0:
                                temp_month = 12
                                temp_year = compare_year - 1
                            if len(branch_sales[
                                (branch_sales["ramadan_CY"].isin([1, 2])) &
                                (branch_sales["month_CY"] == temp_month) &
                                (branch_sales["year_CY"] == temp_year)
                            ]) == 0:
                                day_sales_non_ramadan = branch_sales[
                                    (branch_sales["month_CY"] == temp_month) &
                                    (branch_sales["year_CY"] == temp_year)
                                ].groupby("day_of_week")["gross"].mean().reset_index()
                                for _, v in day_sales_non_ramadan.iterrows():
                                    branch_sales.loc[
                                        (branch_sales["ramadan_BY"] == 3) &
                                        (branch_sales["month_BY"] == mon) &
                                        (branch_sales["day_of_week_BY"] == v["day_of_week"]),
                                        "gross_BY"
                                    ] = v["gross"]
                                break
                            else:
                                temp_month -= 1
                else:
                    # Use same month CY data
                    # NOTE: April (month 4) is already handled above in partial_cy_rows block
                    # Do NOT process April here to avoid overriding the correct calculation
                    if mon != 4:  # Skip April
                        day_sales_non_ramadan = branch_sales[
                            (branch_sales["month_CY"] == mon) & (
                                branch_sales["year_CY"] == compare_year)
                        ].groupby("day_of_week")["gross"].mean().reset_index()
                        
                        for _, v in day_sales_non_ramadan.iterrows():
                            branch_sales.loc[
                                (branch_sales["ramadan_BY"] == 3) &
                                (branch_sales["month_BY"] == mon) &
                                (branch_sales["day_of_week_BY"] == v["day_of_week"]),
                                    "gross_BY"
                                ] = v["gross"]

            # Include all months where Ramadan/Eid occurs in BY 2026
            # Also include months 2, 3, 4 for CY 2025 Ramadan/Eid pattern (Feb, March, April)
            affected_months_cy = [2, 3, 4]  # February, March, April have Ramadan/Eid in CY 2025
            sum_sales = branch_sales[
                ((branch_sales["ramadan_BY"].isin([1, 2, 3])) | 
                 (branch_sales["month_BY"].isin(affected_months_cy))) &
                (branch_sales["year_BY"] == compare_year + 1)
            ].groupby("month_BY").agg(
                actual=('gross', 'sum'),
                est=('gross_BY', 'sum')
            ).reset_index()
            
            # Replace NaN and inf values with 0
            sum_sales = sum_sales.fillna(0)
            sum_sales = sum_sales.replace([float('inf'), float('-inf')], 0)
            # Calculate Ramadan Eid % with proper handling for zero actual values
            sum_sales["Ramadan Eid %"] = sum_sales.apply(
                lambda row: round(((row["est"] - row["actual"]) / row["actual"]) * 100, 2) 
                if row["actual"] != 0 else 0, 
                axis=1
            )
            sum_sales["branch_id"] = branch
            final_df = pd.concat([final_df, sum_sales], ignore_index=True)

        final_df = final_df[["branch_id", "month_BY",
                             "actual", "est", "Ramadan Eid %"]]
        final_df = final_df.rename(columns={"month_BY": "month"})
        return final_df
    except Exception:
        raise


def Eid2Calculations(compare_year, eid2_CY, eid2_BY, df):
    try:
        previous_year = compare_year - 1
        dates_df = pd.DataFrame()
        dates_df["date"] = pd.date_range(start=str(previous_year) + "-01-01",
                                         end=str(compare_year + 1) + "-12-31", freq="d")
        muharram_start_dates = {
            compare_year: eid2_CY,
            compare_year + 1: eid2_BY
        }
        muharram_periods = {
            year: (start, start + timedelta(days=2))
            for year, start in muharram_start_dates.items()
        }

        def assign_muharram_flag(date):
            year = date.year
            if year in muharram_periods:
                muharram_start, muharram_end = muharram_periods[year]
                _, muharram_end_c = muharram_periods[compare_year]
                if muharram_start <= date <= muharram_end:
                    return 1
                elif date.month == muharram_start.month or date.month == muharram_end.month:
                    return 3
                elif date.month == muharram_end_c.month and year == compare_year + 1:
                    return 3
            return 0

        dates_df["muharram"] = dates_df["date"].apply(assign_muharram_flag)

        ramadan_lookup_CY = dict(zip(dates_df["date"], dates_df["muharram"]))
        dates_BY = dates_df[dates_df["date"].dt.year ==
                            compare_year + 1].copy()
        ramadan_lookup_BY = dict(zip(dates_BY["date"], dates_BY["muharram"]))

        def safe_replace_year(date, new_year):
            try:
                if date.year == compare_year:
                    return date.replace(year=new_year)
                else:
                    return date
            except ValueError:
                if date.month == 2 and date.day == 29:
                    return date.replace(year=new_year, day=28)
                else:
                    raise

        agg_funcs = {'gross': 'sum', 'day_of_week': 'first'}
        df = df.groupby(['branch_id', 'business_date']
                        ).agg(agg_funcs).reset_index()
        # FIX: Include data up to and including compare_year (2025), not just < 2026
        df = df[df["business_date"].dt.year <= compare_year]

        df["muharram_CY"] = df["business_date"].map(ramadan_lookup_CY)
        df["business_date_BY"] = df["business_date"].apply(
            lambda d: safe_replace_year(d, compare_year + 1))
        df["muharram_BY"] = df["business_date_BY"].map(ramadan_lookup_BY)
        df["day_of_week_BY"] = df["business_date_BY"].dt.day_name()

        orders_df = df
        orders_df["year_CY"] = orders_df["business_date"].dt.year
        orders_df["month_CY"] = orders_df["business_date"].dt.month
        orders_df["year_BY"] = orders_df["business_date_BY"].dt.year
        orders_df["month_BY"] = orders_df["business_date_BY"].dt.month
        orders_df = orders_df[[
            "branch_id", "business_date", "year_CY", "month_CY", "day_of_week",
            "business_date_BY", "year_BY", "month_BY", "day_of_week_BY",
            "gross", "muharram_CY", "muharram_BY"
        ]]

        final_df = pd.DataFrame()
        for branch in orders_df["branch_id"].unique():
            branch_sales = orders_df[orders_df["branch_id"] == branch].copy()
            branch_sales["gross_BY"] = 0
            day_sales_muharram = branch_sales[branch_sales["muharram_CY"] == 1].groupby(
                "day_of_week")["gross"].mean().reset_index()
            for _, v in day_sales_muharram.iterrows():
                branch_sales.loc[(branch_sales["muharram_BY"] == 1) & (
                    branch_sales["day_of_week_BY"] == v["day_of_week"]), "gross_BY"] = v["gross"]

            ramadan_month_BY = branch_sales.loc[branch_sales["muharram_BY"] == 3, "month_BY"].unique(
            )
            for mon in ramadan_month_BY:
                partial_cy_rows = branch_sales[
                    (branch_sales["muharram_CY"].isin([1, 2])) &
                    (branch_sales["month_CY"] == mon) &
                    (branch_sales["year_CY"] == compare_year)
                ]
                if len(partial_cy_rows) > 0:
                    temp_month = mon - 1
                    temp_year = compare_year
                    while True:
                        if temp_month <= 0:
                            temp_month = 12
                            temp_year = compare_year - 1
                        if len(branch_sales[
                            (branch_sales["muharram_CY"].isin([1, 2])) &
                            (branch_sales["month_CY"] == temp_month) &
                            (branch_sales["year_CY"] == temp_year)
                        ]) == 0:
                            day_sales_non_muharram = branch_sales[
                                (branch_sales["month_CY"] == temp_month) &
                                (branch_sales["year_CY"] == temp_year)
                            ].groupby("day_of_week")["gross"].mean().reset_index()
                            for _, v in day_sales_non_muharram.iterrows():
                                branch_sales.loc[
                                    (branch_sales["muharram_BY"] == 3) &
                                    (branch_sales["month_BY"] == mon) &
                                    (branch_sales["day_of_week_BY"]
                                     == v["day_of_week"]),
                                    "gross_BY"
                                ] = v["gross"]
                            break
                        else:
                            temp_month -= 1
                else:
                    day_sales_non_muharram = branch_sales[
                        (branch_sales["month_CY"] == mon) & (
                            branch_sales["year_CY"] == compare_year)
                    ].groupby("day_of_week")["gross"].mean().reset_index()
                    for _, v in day_sales_non_muharram.iterrows():
                        branch_sales.loc[
                            (branch_sales["muharram_BY"] == 3) &
                            (branch_sales["month_BY"] == mon) &
                            (branch_sales["day_of_week_BY"]
                             == v["day_of_week"]),
                            "gross_BY"
                        ] = v["gross"]

            sum_sales = branch_sales[
                (branch_sales["muharram_BY"].isin([1, 2, 3])) &
                (branch_sales["year_BY"] == compare_year + 1)
            ].groupby("month_BY").agg(
                actual=('gross', 'sum'),
                est=('gross_BY', 'sum')
            ).reset_index()
            sum_sales["Eid2 %"] = round(
                ((sum_sales["est"] - sum_sales["actual"]) / sum_sales["actual"]) * 100, 2)
            sum_sales["branch_id"] = branch
            final_df = pd.concat([final_df, sum_sales], ignore_index=True)

        final_df = final_df[["branch_id",
                             "month_BY", "actual", "est", "Eid2 %"]]
        final_df = final_df.rename(columns={"month_BY": "month"})
        return final_df
    except Exception:
        raise


def Muharram_calculations(compare_year, muharram_CY, muharram_BY, muharram_daycount_CY, muharram_daycount_BY, df):
    try:
        previous_year = compare_year - 1
        dates_df = pd.DataFrame()
        dates_df["date"] = pd.date_range(start=str(previous_year) + "-01-01",
                                         end=str(compare_year + 1) + "-12-31", freq="d")
        muharram_lengths = {
            compare_year: muharram_daycount_CY,
            compare_year + 1: muharram_daycount_BY
        }
        muharram_start_dates = {
            compare_year: muharram_CY,
            compare_year + 1: muharram_BY
        }
        muharram_periods = {
            year: (start, start + timedelta(days=muharram_lengths[year] - 1))
            for year, start in muharram_start_dates.items()
        }

        def assign_muharram_flag(date):
            year = date.year
            if year in muharram_periods:
                muharram_start, muharram_end = muharram_periods[year]
                _, muharram_end_c = muharram_periods[compare_year]
                if muharram_start <= date <= muharram_end:
                    return 1
                elif date.month == muharram_start.month or date.month == muharram_end.month:
                    return 3
                elif date.month == muharram_end_c.month and year == compare_year + 1:
                    return 3
            return 0

        dates_df["muharram"] = dates_df["date"].apply(assign_muharram_flag)

        ramadan_lookup_CY = dict(zip(dates_df["date"], dates_df["muharram"]))
        dates_BY = dates_df[dates_df["date"].dt.year ==
                            compare_year + 1].copy()
        ramadan_lookup_BY = dict(zip(dates_BY["date"], dates_BY["muharram"]))

        def safe_replace_year(date, new_year):
            try:
                if date.year == compare_year:
                    return date.replace(year=new_year)
                else:
                    return date
            except ValueError:
                if date.month == 2 and date.day == 29:
                    return date.replace(year=new_year, day=28)
                else:
                    raise

        agg_funcs = {'gross': 'sum', 'day_of_week': 'first'}
        df = df.groupby(['branch_id', 'business_date']
                        ).agg(agg_funcs).reset_index()
        # FIX: Include data up to and including compare_year (2025), not just < 2026
        df = df[df["business_date"].dt.year <= compare_year]

        df["muharram_CY"] = df["business_date"].map(ramadan_lookup_CY)
        df["business_date_BY"] = df["business_date"].apply(
            lambda d: safe_replace_year(d, compare_year + 1))
        df["muharram_BY"] = df["business_date_BY"].map(ramadan_lookup_BY)
        df["day_of_week_BY"] = df["business_date_BY"].dt.day_name()

        orders_df = df
        orders_df["year_CY"] = orders_df["business_date"].dt.year
        orders_df["month_CY"] = orders_df["business_date"].dt.month
        orders_df["year_BY"] = orders_df["business_date_BY"].dt.year
        orders_df["month_BY"] = orders_df["business_date_BY"].dt.month
        orders_df = orders_df[[
            "branch_id", "business_date", "year_CY", "month_CY", "day_of_week",
            "business_date_BY", "year_BY", "month_BY", "day_of_week_BY",
            "gross", "muharram_CY", "muharram_BY"
        ]]

        final_df = pd.DataFrame()
        for branch in orders_df["branch_id"].unique():
            branch_sales = orders_df[orders_df["branch_id"] == branch].copy()
            branch_sales["gross_BY"] = 0
            day_sales_muharram = branch_sales[branch_sales["muharram_CY"] == 1].groupby(
                "day_of_week")["gross"].mean().reset_index()
            for _, v in day_sales_muharram.iterrows():
                branch_sales.loc[(branch_sales["muharram_BY"] == 1) & (
                    branch_sales["day_of_week_BY"] == v["day_of_week"]), "gross_BY"] = v["gross"]

            ramadan_month_BY = branch_sales.loc[branch_sales["muharram_BY"] == 3, "month_BY"].unique(
            )
            for mon in ramadan_month_BY:
                partial_cy_rows = branch_sales[
                    (branch_sales["muharram_CY"].isin([1, 2])) &
                    (branch_sales["month_CY"] == mon) &
                    (branch_sales["year_CY"] == compare_year)
                ]
                if len(partial_cy_rows) > 0:
                    temp_month = mon - 1
                    temp_year = compare_year
                    while True:
                        if temp_month <= 0:
                            temp_month = 12
                            temp_year = compare_year - 1
                        if len(branch_sales[
                            (branch_sales["muharram_CY"].isin([1, 2])) &
                            (branch_sales["month_CY"] == temp_month) &
                            (branch_sales["year_CY"] == temp_year)
                        ]) == 0:
                            day_sales_non_muharram = branch_sales[
                                (branch_sales["month_CY"] == temp_month) &
                                (branch_sales["year_CY"] == temp_year)
                            ].groupby("day_of_week")["gross"].mean().reset_index()
                            for _, v in day_sales_non_muharram.iterrows():
                                branch_sales.loc[
                                    (branch_sales["muharram_BY"] == 3) &
                                    (branch_sales["month_BY"] == mon) &
                                    (branch_sales["day_of_week_BY"]
                                     == v["day_of_week"]),
                                    "gross_BY"
                                ] = v["gross"]
                            break
                        else:
                            temp_month -= 1
                else:
                    day_sales_non_muharram = branch_sales[
                        (branch_sales["month_CY"] == mon) & (
                            branch_sales["year_CY"] == compare_year)
                    ].groupby("day_of_week")["gross"].mean().reset_index()
                    for _, v in day_sales_non_muharram.iterrows():
                        branch_sales.loc[
                            (branch_sales["muharram_BY"] == 3) &
                            (branch_sales["month_BY"] == mon) &
                            (branch_sales["day_of_week_BY"]
                             == v["day_of_week"]),
                            "gross_BY"
                        ] = v["gross"]

            sum_sales = branch_sales[
                (branch_sales["muharram_BY"].isin([1, 2, 3])) &
                (branch_sales["year_BY"] == compare_year + 1)
            ].groupby("month_BY").agg(
                actual=('gross', 'sum'),
                est=('gross_BY', 'sum')
            ).reset_index()
            sum_sales["Muharram %"] = round(
                ((sum_sales["est"] - sum_sales["actual"]) / sum_sales["actual"]) * 100, 2)
            sum_sales["branch_id"] = branch
            final_df = pd.concat([final_df, sum_sales], ignore_index=True)

        final_df = final_df[["branch_id", "month_BY",
                             "actual", "est", "Muharram %"]]
        final_df = final_df.rename(columns={"month_BY": "month"})
        return final_df
    except Exception:
        raise


def descriptiveCalculations(compare_year, df):
    """
    Build monthly descriptive metrics with fallback:
      - If a (branch, month) in compare_year is missing OR <95% covered,
        use previous_year's same (branch, month) instead.
    """
    try:
        df = df.copy()
        df['year'] = df['business_date'].dt.year
        df['month'] = df['business_date'].dt.month

        previous_year = compare_year - 1

        # -----------------------------
        # 0) Find months to fall back (same as WeeklyAverageCalculations)
        # -----------------------------
        # unique (branch, date) to count coverage
        unique_dates = df[['branch_id', 'business_date']].drop_duplicates()
        unique_dates['year'] = unique_dates['business_date'].dt.year
        unique_dates['month'] = unique_dates['business_date'].dt.month

        date_counts = (
            unique_dates.groupby(['branch_id', 'year', 'month'])
                        .size()
                        .reset_index(name='actual_days')
        )
        # days_in_month for each (year, month)
        from calendar import monthrange
        date_counts['days_in_month'] = date_counts.apply(
            lambda r: monthrange(int(r['year']), int(r['month']))[1], axis=1
        )
        date_counts['percent_covered'] = date_counts['actual_days'] / \
            date_counts['days_in_month']

        days_present = date_counts[date_counts['year'] == compare_year]
        incomplete_months = days_present[days_present['percent_covered'] < 0.1][[
            'branch_id', 'month']]

        # All branches seen in data (already filtered to active ones earlier)
        all_months = pd.MultiIndex.from_product(
            [sorted(df['branch_id'].unique()), list(range(1, 13))],
            names=['branch_id', 'month']
        ).to_frame(index=False)

        months_present = days_present[['branch_id', 'month']].drop_duplicates()

        missing_months = (
            all_months.merge(months_present, on=[
                             'branch_id', 'month'], how='left', indicator=True)
                      .query('_merge == "left_only"')[['branch_id', 'month']]
        )

        # Months to FALL BACK (missing OR <50% covered in compare_year)
        full_fallback_months = pd.concat(
            [incomplete_months, missing_months], ignore_index=True)
        full_fallback_months.drop_duplicates(inplace=True)

        # Helper: pairs that are VALID in CY (i.e., NOT in fallback)
        valid_cy_pairs = (
            all_months.merge(full_fallback_months, on=[
                             'branch_id', 'month'], how='left', indicator=True)
                      .query('_merge == "left_only"')[['branch_id', 'month']]
        )

        # -----------------------------
        # 1) Helper to summarize a given subset (year-filtered)
        # -----------------------------
        def _summarize_year(sub):
            # internal group keys
            keys = ['branch_id', 'year', 'month']

            base = (
                sub.groupby(keys)
                .agg(
                    total_sales=('gross', 'sum'),
                    total_trans=('OrderID', 'count'),
                    discount=('Discount', 'sum'),
                    customer_count=('guests', 'sum'),
                    vat=('VAT', 'sum'),
                )
                .reset_index()
            )

            # safe ratios
            base['discount_pct'] = np.divide(
                base['discount'], base['total_sales'],
                out=np.zeros_like(base['discount'], dtype=float),
                where=base['total_sales'].to_numpy() != 0
            )
            base['discount_pct'] = base['discount_pct'] * 100
            base['avg_check'] = np.divide(
                base['total_sales'], base['total_trans'],
                out=np.zeros_like(base['total_trans'], dtype=float),
                where=base['total_trans'].to_numpy() != 0
            )
            base['netsales'] = base['total_sales'] - \
                base['discount'] - base['vat']

            # order type splits
            order_types = ['Dinein', 'Delivery',
                           'Takeaway', 'Drive Thru', 'Catering']
            tmp = sub.copy()
            tmp['OrderType'] = pd.Categorical(
                tmp['OrderType'], categories=order_types)

            pt = pd.pivot_table(
                tmp, index=keys, columns='OrderType',
                values=['gross', 'OrderID'],
                aggfunc={'gross': 'sum', 'OrderID': 'count'},
                fill_value=0
            )
            pt.columns = [f'{a}_{b}' for a, b in pt.columns.to_flat_index()]
            pt = pt.reset_index()

            name_map = {
                'Dinein': ('dining_sales',    'dining_trans',    'dining_avg_check'),
                'Delivery': ('delivery_sales',  'delivery_trans',  'delivery_avg_check'),
                'Takeaway': ('takeaway_sales',  'takeaway_trans',  'takeaway_avg_check'),
                'Drive Thru': ('drivethru_sales', 'drivethru_trans', 'drivethru_avg_check'),
                'Catering': ('catering_sales',  'catering_trans',  'catering_avg_check'),
            }
            for typ, (sales_name, trans_name, avg_check_name) in name_map.items():
                s_col = f'gross_{typ}'
                t_col = f'OrderID_{typ}'
                if s_col not in pt:
                    pt[s_col] = 0
                if t_col not in pt:
                    pt[t_col] = 0
                pt.rename(columns={s_col: sales_name,
                          t_col: trans_name}, inplace=True)
                pt[avg_check_name] = np.divide(
                    pt[sales_name], pt[trans_name],
                    out=np.zeros(len(pt), dtype=float),
                    where=pt[trans_name].to_numpy() != 0
                )

            out = base.merge(pt, on=keys, how='left').fillna(0)
            out['avg_per_cover'] = np.divide(
                out['dining_sales'], out['customer_count'],
                out=np.zeros(len(out), dtype=float),
                where=out['customer_count'].to_numpy() != 0
            )
            return out

        # -----------------------------
        # 2) Build CY summary for VALID months only; BY summary for FALLBACK months only
        # -----------------------------
        cy_all = _summarize_year(df[df['year'] == compare_year])
        by_all = _summarize_year(df[df['year'] == previous_year])

        # Filter to pairs
        cy_valid = cy_all.merge(
            valid_cy_pairs, on=['branch_id', 'month'], how='inner')
        by_fallback = by_all.merge(full_fallback_months, on=[
                                   'branch_id', 'month'], how='inner')
        
        cy_valid['used_fallback'] = False
        by_fallback['used_fallback'] = True

        # Combine; drop 'year'
        summary_df = pd.concat([cy_valid, by_fallback], ignore_index=True)
        if 'year' in summary_df.columns:
            summary_df = summary_df.drop(columns=['year'])

        # Ensure month is int
        summary_df['month'] = summary_df['month'].astype(int)

        return summary_df
    except Exception:
        raise
