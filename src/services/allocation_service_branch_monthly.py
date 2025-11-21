from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func
from src.core.db import get_session, close_session
from src.db.dbtables import ProjectionEstimate
from src.db.projection_allocation import ProjectionEstimateAdjusted
from src.models.projected_allocation_branch_monthly import (
    BranchMonthlyTotalsIn, BranchMonthlyTotalsOut, BranchMonthlyAllocationResult
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

def _copy_baseline_pair(dbs, branch_id: int, month: int) -> tuple[int,int,float]:
    """Copy single (branch, month) from baseline to adjusted (factor=1)."""
    rows = dbs.query(ProjectionEstimate)\
              .filter(ProjectionEstimate.branch_id == branch_id,
                      ProjectionEstimate.month == month).all()
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

def allocate_branch_monthly_totals(payload: BranchMonthlyTotalsIn, include_data: bool = False) -> BranchMonthlyTotalsOut:
    dbs = get_session()
    results = []
    overall_rows_considered = 0
    overall_rows_written = 0
    overall_baseline_sum = 0.0
    pairs_with_allocation = 0

    try:
        # Gather all existing (branch, month) pairs from baseline
        all_pairs = set((r.branch_id, int(r.month)) for r in dbs.query(ProjectionEstimate).all())

        # 1) Apply requested factors per (branch, month)
        for bid, months in sorted(payload.branch_month_totals.items(), key=lambda kv: kv[0]):
            for m, target in sorted(months.items(), key=lambda kv: kv[0]):
                rows = dbs.query(ProjectionEstimate)\
                          .filter(ProjectionEstimate.branch_id == bid,
                                  ProjectionEstimate.month == m).all()
                rows_considered = len(rows)
                baseline_sum = sum(float(r.est_total_sales or 0) for r in rows)
                overall_rows_considered += rows_considered
                overall_baseline_sum += baseline_sum

                if rows_considered == 0:
                    results.append(BranchMonthlyAllocationResult(
                        branch_id=bid, month=m, rows_considered=0, rows_written=0,
                        baseline_sum=0.0, applied_factor=0.0, skipped_zero_baseline=0
                    ))
                    continue

                if not target or baseline_sum <= 0:
                    rows_c, rows_w, base_sum = _copy_baseline_pair(dbs, bid, m)
                    overall_rows_written += rows_w
                    results.append(BranchMonthlyAllocationResult(
                        branch_id=bid, month=m, rows_considered=rows_c, rows_written=rows_w,
                        baseline_sum=float(base_sum), applied_factor=1.0, skipped_zero_baseline=0
                    ))
                else:
                    factor = float(target) / float(baseline_sum)
                    pairs_with_allocation += 1
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
                    results.append(BranchMonthlyAllocationResult(
                        branch_id=bid, month=m, rows_considered=rows_considered, rows_written=rows_written,
                        baseline_sum=float(baseline_sum), applied_factor=factor, skipped_zero_baseline=0
                    ))

        # 2) All pairs NOT provided ⇒ factor=1 (recompute from baseline)
        requested_pairs = set(
            (int(bid), int(m))
            for bid, ms in payload.branch_month_totals.items()
            for m in ms.keys()
        )
        missing_pairs = all_pairs - requested_pairs
        for (bid, m) in sorted(missing_pairs):
            rows_c, rows_w, base_sum = _copy_baseline_pair(dbs, bid, m)
            overall_rows_considered += rows_c
            overall_rows_written += rows_w
            overall_baseline_sum += float(base_sum)
            results.append(BranchMonthlyAllocationResult(
                branch_id=bid, month=m, rows_considered=rows_c, rows_written=rows_w,
                baseline_sum=float(base_sum), applied_factor=1.0, skipped_zero_baseline=0
            ))

        dbs.commit()

        out = BranchMonthlyTotalsOut(
            results=sorted(results, key=lambda r: (r.branch_id, r.month)),
            overall_rows_considered=overall_rows_considered,
            overall_rows_written=overall_rows_written,
            overall_baseline_sum=overall_baseline_sum,
            pairs_requested=len(requested_pairs),
            pairs_with_allocation=pairs_with_allocation,
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
