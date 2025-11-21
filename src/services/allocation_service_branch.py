from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func
from collections import defaultdict
from src.core.db import get_session, close_session
from src.db.dbtables import ProjectionEstimate
from src.db.projection_allocation import ProjectionEstimateAdjusted
from src.models.projected_allocation_branch import (
    BranchTotalsIn, BranchTotalsOut, BranchAllocationResult
)
from src.services.grouped_payload import build_grouped_payload

DONT_TOUCH = {"id", "created_at", "updated_at"}
NUMERIC_COLS = {
    "est_dine_sales","est_dine_trans","est_customer_count","est_dine_avg_check","est_avg_per_cover",
    "est_delivery_sales","est_delivery_trans","est_delivery_avg_check",
    "est_takeway_sales","est_takeway_trans","est_takeway_avg_check",
    "est_drivethru_sales","est_drivethru_trans","est_drivethru_avg_check",
    "est_catering_sales","est_catering_trans","est_catering_avg_check",
    "est_total_sales","est_total_trans","est_total_avg",
    "est_total_discount","est_discount_pct","est_vat","est_net_sales",
}
COPY_AS_IS_COLS = {
    # averages
    "est_total_avg", "est_dine_avg_check", "est_avg_per_cover",
    "est_delivery_avg_check", "est_takeway_avg_check",
    "est_drivethru_avg_check", "est_catering_avg_check",
    # percentages
    "est_discount_pct",
    # transactions + counts (recomputed later in grouped payload)
    "est_total_trans", "est_dine_trans", "est_delivery_trans",
    "est_takeway_trans", "est_drivethru_trans", "est_catering_trans",
    "est_customer_count"
}

def _scale_value(col: str, v, factor: float):
    if v is None:
        return None
    if col in COPY_AS_IS_COLS:
        try: return float(v)
        except Exception: return v
    try: return float(v) * factor
    except Exception: return v

def _copy_baseline_branch(dbs, branch_id: int) -> tuple[int,int,float]:
    """Copy all months for branch from baseline to adjusted (factor=1). returns (rows_considered, rows_written, baseline_sum)."""
    rows = dbs.query(ProjectionEstimate).filter(ProjectionEstimate.branch_id == branch_id).all()
    baseline_sum = sum(float(r.est_total_sales or 0) for r in rows)
    written = 0
    for r in rows:
        vals = {}
        for col in ProjectionEstimateAdjusted.__table__.columns.keys():
            if col in DONT_TOUCH: continue
            if hasattr(r, col):
                v = getattr(r, col)
                vals[col] = _scale_value(col, v, 1.0) if col in NUMERIC_COLS else v
        ins = pg_insert(ProjectionEstimateAdjusted).values(**vals)
        stmt = ins.on_conflict_do_update(
            index_elements=['branch_id', 'month'],
            set_={k: getattr(ins.excluded, k) for k in vals.keys() if k not in ('branch_id','month')}
        )
        dbs.execute(stmt); written += 1
    return (len(rows), written, baseline_sum)

def allocate_branch_totals(payload: BranchTotalsIn, include_data: bool = False) -> BranchTotalsOut:
    dbs = get_session()
    results = []
    overall_rows_considered = 0
    overall_rows_written = 0
    overall_baseline_sum = 0.0
    branches_with_allocation = 0

    try:
        # Preload baseline grouped by branch
        branch_to_rows = defaultdict(list)
        for r in dbs.query(ProjectionEstimate).all():
            branch_to_rows[r.branch_id].append(r)

        all_branch_ids = set(branch_to_rows.keys())
        requested = payload.branch_totals  # {branch_id: Optional[float]}

        # 1) Handle branches explicitly mentioned
        for bid, target in requested.items():
            rows = branch_to_rows.get(bid, [])
            rows_considered = len(rows)
            baseline_sum = sum(float(x.est_total_sales or 0) for x in rows)
            overall_rows_considered += rows_considered
            overall_baseline_sum += baseline_sum

            if rows_considered == 0:
                results.append(BranchAllocationResult(
                    branch_id=bid, rows_considered=0, rows_written=0,
                    baseline_sum=0.0, applied_factor=0.0, skipped_zero_baseline=0
                ))
                continue

            if not target or baseline_sum <= 0:
                # factor = 1 (recompute baseline)
                rows_c, rows_w, base_sum = _copy_baseline_branch(dbs, bid)
                overall_rows_written += rows_w
                results.append(BranchAllocationResult(
                    branch_id=bid, rows_considered=rows_c, rows_written=rows_w,
                    baseline_sum=float(base_sum), applied_factor=1.0, skipped_zero_baseline=0
                ))
                continue

            factor = float(target) / float(baseline_sum)
            branches_with_allocation += 1

            rows_written = 0
            for r in rows:
                vals = {}
                for col in ProjectionEstimateAdjusted.__table__.columns.keys():
                    if col in DONT_TOUCH: continue
                    if hasattr(r, col):
                        v = getattr(r, col)
                        vals[col] = _scale_value(col, v, factor) if col in NUMERIC_COLS else v
                ins = pg_insert(ProjectionEstimateAdjusted).values(**vals)
                stmt = ins.on_conflict_do_update(
                    index_elements=['branch_id', 'month'],
                    set_={k: getattr(ins.excluded, k) for k in vals.keys() if k not in ('branch_id','month')}
                )
                dbs.execute(stmt); rows_written += 1

            overall_rows_written += rows_written
            results.append(BranchAllocationResult(
                branch_id=bid, rows_considered=rows_considered, rows_written=rows_written,
                baseline_sum=float(baseline_sum), applied_factor=factor, skipped_zero_baseline=0
            ))

        # 2) Branches NOT mentioned ⇒ factor=1 (recompute from baseline)
        missing_branches = all_branch_ids - set(requested.keys())
        for bid in sorted(missing_branches):
            rows_c, rows_w, base_sum = _copy_baseline_branch(dbs, bid)
            overall_rows_considered += rows_c
            overall_rows_written += rows_w
            overall_baseline_sum += float(base_sum)
            results.append(BranchAllocationResult(
                branch_id=bid, rows_considered=rows_c, rows_written=rows_w,
                baseline_sum=float(base_sum), applied_factor=1.0, skipped_zero_baseline=0
            ))

        dbs.commit()

        out = BranchTotalsOut(
            results=sorted(results, key=lambda r: r.branch_id),
            overall_rows_considered=overall_rows_considered,
            overall_rows_written=overall_rows_written,
            overall_baseline_sum=overall_baseline_sum,
            branches_requested=len(requested),
            branches_with_allocation=branches_with_allocation,
            data=None
        )
        if include_data:
            out.data = build_grouped_payload()
        return out

    except Exception:
        dbs.rollback()
        raise
    finally:
        close_session(dbs)
