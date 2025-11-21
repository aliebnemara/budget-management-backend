# services/grouped_payload.py
from typing import List, Dict, Any, DefaultDict
from collections import defaultdict
from sqlalchemy.orm import joinedload
from src.core.db import get_session, close_session
from src.db.dbtables import Brand, Branch, BudgetRuntimeState, ProjectionInput
from src.db.projection_allocation import ProjectionEstimateAdjusted
import math

NUMERIC_MONTH_KEYS = [
    "total_sales", "total_trans", "avg_check", "discount", "discount_pct", "vat", "netsales",
    "dining_sales", "dining_trans", "dining_avg_check", "avg_per_cover", "customer_count",
    "delivery_sales", "delivery_trans", "delivery_avg_check",
    "takeaway_sales", "takeaway_trans", "takeaway_avg_check",
    "drivethru_sales", "drivethru_trans", "drivethru_avg_check",
    "catering_sales", "catering_trans", "catering_avg_check",
    "trade_on_off", "ramadan_eid_pct", "muharram_pct", "eid2_pct",
]

INPUT_KEYS = [
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
]

EST_KEYS = [
    "est_total_sales", "est_total_trans", "est_total_avg",
    "est_total_discount", "est_discount_pct", "est_vat", "est_net_sales",
    "est_dine_sales", "est_dine_trans", "est_customer_count",
    "est_dine_avg_check", "est_avg_per_cover",
    "est_delivery_sales", "est_delivery_trans", "est_delivery_avg_check",
    "est_takeway_sales", "est_takeway_trans", "est_takeway_avg_check",
    "est_drivethru_sales", "est_drivethru_trans", "est_drivethru_avg_check",
    "est_catering_sales", "est_catering_trans", "est_catering_avg_check",
]


def _safe(v):
    try:
        if v is None:
            return None
        # handle Decimal as well
        return float(v)
    except Exception:
        return v


# ---------- transactions recompute helpers ----------
DERIVED_TRANS_RULES = [
    ("est_total_sales",     "est_total_avg",          "est_total_trans"),
    ("est_dine_sales",      "est_dine_avg_check",     "est_dine_trans"),
    ("est_dine_sales",      "est_avg_per_cover",     "est_customer_count"),
    ("est_delivery_sales",  "est_delivery_avg_check", "est_delivery_trans"),
    ("est_takeway_sales",   "est_takeway_avg_check",  "est_takeway_trans"),
    ("est_drivethru_sales", "est_drivethru_avg_check","est_drivethru_trans"),
    ("est_catering_sales",  "est_catering_avg_check", "est_catering_trans"),
]

def _round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))

def _recompute_transactions_inplace(row: Dict[str, Any]) -> None:
    """
    Keep averages fixed; recompute transactions as round(sales / avg).
    If sales or avg is None/0, set transactions to None.
    """
    for sales_key, avg_key, trans_key in DERIVED_TRANS_RULES:
        s = row.get(sales_key)
        a = row.get(avg_key)
        if s is None or a in (None, 0):
            row[trans_key] = None
            continue
        try:
            row[trans_key] = _round_half_up(float(s) / float(a))
        except Exception:
            row[trans_key] = None
# ---------------------------------------------------


def _baseline_from_runtime_state(dbs) -> Dict[int, Dict[int, Dict[str, Any]]]:
    """
    Build: baseline_map[branch_id][month] = {NUMERIC_MONTH_KEYS...}
    from budget_runtime_state.result_json (brands -> branches -> months).
    Accepts payload as either dict (with "data"/"brands") or list of brand dicts.
    """
    baseline_map: DefaultDict[int, Dict[int, Dict[str, Any]]] = defaultdict(dict)

    state = dbs.query(BudgetRuntimeState).order_by(
        BudgetRuntimeState.updated_at.desc()
    ).first()
    if not state or not state.result_json:
        return baseline_map

    payload = state.result_json  # JSONB → Python object (dict or list)

    # Normalize to a list of brand dicts
    if isinstance(payload, dict):
        brands = payload.get("data") or payload.get("brands") or []
    elif isinstance(payload, list):
        brands = payload
    else:
        return baseline_map

    for brand in brands:
        for br in (brand.get("branches") or []):
            bid = br.get("branch_id")
            if bid is None:
                continue
            for mobj in (br.get("months") or []):
                try:
                    m = int(mobj.get("month"))
                except Exception:
                    continue
                row = {}
                for k in NUMERIC_MONTH_KEYS:
                    if k in mobj:
                        row[k] = _safe(mobj.get(k))
                baseline_map[bid][m] = row
    return baseline_map


def build_grouped_payload(include_baseline: bool = True) -> List[Dict[str, Any]]:
    dbs = get_session()
    try:
        brands = dbs.query(Brand).options(joinedload(Brand.branches)).filter(Brand.is_deleted == False).order_by(Brand.id).all()

        # 1) inputs
        inputs_map: DefaultDict[int, Dict[int, Dict[str, Any]]] = defaultdict(dict)
        for pi in dbs.query(ProjectionInput).all():
            m = inputs_map[pi.branch_id].setdefault(int(pi.month), {})
            for k in INPUT_KEYS:
                if hasattr(pi, k):
                    m[k] = _safe(getattr(pi, k))

        # 2) baseline/actuals – respect the flag
        if include_baseline:
            baseline_map = _baseline_from_runtime_state(dbs)
        else:
            baseline_map = defaultdict(dict)  # type: ignore[var-annotated]

        # 3) adjusted estimates
        adjusted_map: DefaultDict[int, Dict[int, Dict[str, Any]]] = defaultdict(dict)
        for ae in dbs.query(ProjectionEstimateAdjusted).all():
            m = adjusted_map[ae.branch_id].setdefault(int(ae.month), {})
            for k in EST_KEYS:
                if hasattr(ae, k):
                    m[k] = _safe(getattr(ae, k))

        # 4) assemble
        out: List[Dict[str, Any]] = []
        for b in brands:
            bobj = {"brand_id": b.id, "brand_name": b.name, "branches": []}
            # Filter out soft-deleted branches
            active_branches = [br for br in b.branches if not br.is_deleted]
            for br in sorted(active_branches, key=lambda x: x.id):
                seen_months = (
                    set(baseline_map.get(br.id, {}).keys())
                    | set(inputs_map.get(br.id, {}).keys())
                    | set(adjusted_map.get(br.id, {}).keys())
                )
                months = []
                for m in sorted(seen_months):
                    row = {"month": m}
                    # baseline first
                    for k in NUMERIC_MONTH_KEYS:
                        row[k] = baseline_map.get(br.id, {}).get(m, {}).get(k)
                    # inputs next
                    for k in INPUT_KEYS:
                        row[k] = inputs_map.get(br.id, {}).get(m, {}).get(k)
                    # adjusted estimations
                    for k in EST_KEYS:
                        row[k] = adjusted_map.get(br.id, {}).get(m, {}).get(k)

                    # Keep averages fixed; recompute transactions from sales/avg
                    _recompute_transactions_inplace(row)
                    VAT_RATE = 0.10  # or whatever your actual rate is (e.g., 0.05 for 5%)
                    sales = row.get("est_total_sales")
                    discount = row.get("est_total_discount") or 0
                    if sales is not None:
                        vat = (sales-discount) * VAT_RATE/1.1
                        row["est_vat"] = round(vat, 2)
                        row["est_net_sales"] = round(sales - discount - vat, 2)
                    else:
                        row["est_vat"] = None
                        row["est_net_sales"] = None
                    months.append(row)
                bobj["branches"].append(
                    {"branch_id": br.id, "branch_name": br.name, "months": months}
                )
            out.append(bobj)
        return out
    finally:
        close_session(dbs)
