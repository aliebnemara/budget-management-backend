# crud/budget_state.py
import json
from typing import Callable, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from src.models.budget import defaultBudgetModel
from src.db.dbtables import BudgetRuntimeState
from src.core.db import get_session, close_session
from src.services.budget import add_projection_inputs, calculateDefault, dataframe_to_brand_json
import pandas as pd
from decimal import Decimal
from copy import deepcopy

# Keys to strip from the result before caching
PROJECTION_KEYS = [
    "dining_sales_pct", "projected_dinin_avg_check", "projected_avg_per_cover",
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
    # only include if you create them in your pipeline:
    # "effective_dinin_avg_check", "effective_avg_per_cover",
    # "effective_delivery_avg_check", "effective_takeaway_avg_check",
    # "effective_drivethru_avg_check", "effective_catering_avg_check",
    # "effective_discount_pct",
]


def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def strip_projection_fields(result_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    temp = convert_decimals(result_json["data"])
    data = deepcopy(temp)
    for brand in data or []:
        for br in brand.get("branches", []):
            for mp in br.get("months", []):
                for k in PROJECTION_KEYS:
                    mp.pop(k, None)
    return data


def inputs_equal(state: BudgetRuntimeState, body: defaultBudgetModel) -> bool:
    """Compare each scalar column; dates compared directly."""
    return (
        state.compare_year == body.compare_year and
        state.ramadan_cy == body.ramadan_CY and
        state.ramadan_by == body.ramadan_BY and
        state.ramadan_daycount_cy == body.ramadan_daycount_CY and
        state.ramadan_daycount_by == body.ramadan_daycount_BY and
        state.muharram_cy == body.muharram_CY and
        state.muharram_by == body.muharram_BY and
        state.muharram_daycount_cy == body.muharram_daycount_CY and
        state.muharram_daycount_by == body.muharram_daycount_BY and
        state.eid2_cy == body.eid2_CY and
        state.eid2_by == body.eid2_BY
    )


def compute_or_reuse(
    body: defaultBudgetModel,
    recompute: Callable[[defaultBudgetModel], List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    # fetch singleton (id=1)
    session = get_session()
    try:
        state = session.get(BudgetRuntimeState, 1)
        if body == None:
            # to_date = lambda d: d.date() if hasattr(d, "date") else d
            body = defaultBudgetModel(
                compare_year=state.compare_year,
                ramadan_CY=state.ramadan_cy,
                ramadan_BY=state.ramadan_by,
                ramadan_daycount_CY=state.ramadan_daycount_cy,
                ramadan_daycount_BY=state.ramadan_daycount_by,
                muharram_CY=state.muharram_cy,
                muharram_BY=state.muharram_by,
                muharram_daycount_CY=state.muharram_daycount_cy,
                muharram_daycount_BY=state.muharram_daycount_by,
                eid2_CY=state.eid2_cy,
                eid2_BY=state.eid2_by,
            )

        # Check if we can use cached data
        # Skip cache if: state doesn't exist, inputs don't match, or result_json is empty/invalid
        if state and inputs_equal(state, body) and state.result_json and len(state.result_json) > 0:
            # Flatten the cached JSON (brand -> branches -> months)
            df_cached = pd.json_normalize(
                state.result_json,
                record_path=['branches', 'months'],
                meta=[['branches', 'branch_id'],
                      ['branches', 'branch_name'],
                      'brand_id',
                      'brand_name'],
                errors='ignore'
            )

            # Rename meta columns to what your code expects
            df_cached = df_cached.rename(columns={
                'branches.branch_id': 'branch_id',
                'branches.branch_name': 'branch_name',
                'Eid2 %': 'eid2_pct',
                'Muharram %': 'muharram_pct',
                'Ramadan Eid %': 'ramadan_eid_pct',
            })

            # Make sure the key columns exist with correct types
            if 'month' not in df_cached.columns:
                # Cache is invalid, force recompute
                print("⚠️  Cache is invalid (missing 'month' field), recomputing...")
            else:
                df_cached['branch_id'] = df_cached['branch_id'].astype(int)
                df_cached['month'] = df_cached['month'].astype(int)
                merged = add_projection_inputs(df_cached)
                # Build the final JSON
                results = dataframe_to_brand_json(merged, body)
                return results

        # Inputs changed or first run → recompute
        fresh = recompute(body)
        # return fresh
        clean = strip_projection_fields(fresh)

        # Upsert the singleton row with the new inputs + result_json
        payload = dict(
            id=1,
            compare_year=body.compare_year,
            ramadan_cy=body.ramadan_CY,
            ramadan_by=body.ramadan_BY,
            ramadan_daycount_cy=body.ramadan_daycount_CY,
            ramadan_daycount_by=body.ramadan_daycount_BY,
            muharram_cy=body.muharram_CY,
            muharram_by=body.muharram_BY,
            muharram_daycount_cy=body.muharram_daycount_CY,
            muharram_daycount_by=body.muharram_daycount_BY,
            eid2_cy=body.eid2_CY,
            eid2_by=body.eid2_BY,
            result_json=clean,
        )

        stmt = insert(BudgetRuntimeState).values(**payload).on_conflict_do_update(
            index_elements=[BudgetRuntimeState.id],
            set_=payload
        )
        session.execute(stmt)
        session.commit()
        return fresh
    except:
        raise
    finally:
        close_session(session)
