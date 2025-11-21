from sqlalchemy.dialects.postgresql import insert as pg_insert
from src.core.db import get_session, close_session
from src.db.dbtables import ProjectionEstimate
from src.db.projection_allocation import ProjectionEstimateAdjusted
from src.models.projected_allocation_monthly import (
    MonthlyTotalsIn, MonthlyTotalsOut, MonthlyAllocationResult
)
from src.services.grouped_payload import build_grouped_payload
from sqlalchemy import func

# Keep consistent with your grand-total service
DONT_TOUCH = {"id", "created_at", "updated_at"}
# Which estimate columns get scaled (same as before)
NUMERIC_COLS = {
    "est_dine_sales", "est_dine_trans", "est_customer_count", "est_avg_per_cover", "est_dine_avg_check",
    "est_delivery_sales", "est_delivery_trans", "est_delivery_avg_check",
    "est_takeway_sales", "est_takeway_trans", "est_takeway_avg_check",
    "est_drivethru_sales", "est_drivethru_trans", "est_drivethru_avg_check",
    "est_catering_sales", "est_catering_trans", "est_catering_avg_check",
    "est_total_sales", "est_total_trans", "est_total_avg",
    "est_total_discount", "est_discount_pct", "est_vat", "est_net_sales",
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


def _upsert_from_baseline_for_month(dbs, month: int) -> int:
    """
    Copy baselines from ProjectionEstimate to ProjectionEstimateAdjusted for the given month (factor=1).
    Returns rows written.
    """
    rows = dbs.query(ProjectionEstimate).filter(
        ProjectionEstimate.month == month).all()
    written = 0
    for r in rows:
        vals = {}
        for col in ProjectionEstimateAdjusted.__table__.columns.keys():
            if col in DONT_TOUCH:
                continue
            if hasattr(r, col):
                v = getattr(r, col)
                # factor = 1 -> copy as-is (still preserve est_discount_pct)
                vals[col] = _scale_value(
                    col, v, 1.0) if col in NUMERIC_COLS else v

        ins = pg_insert(ProjectionEstimateAdjusted).values(**vals)
        stmt = ins.on_conflict_do_update(
            index_elements=['branch_id', 'month'],
            set_={k: getattr(ins.excluded, k)
                  for k in vals.keys() if k not in ('branch_id', 'month')}
        )
        dbs.execute(stmt)
        written += 1
    return written


def _scale_value(col: str, v, factor: float):
    if v is None:
        return None
    # keep percentages as-is
    # if col == "est_discount_pct" or col == "est_total_avg":
    if col in COPY_AS_IS_COLS:
        try:
            return float(v)
        except Exception:
            return v
    # numbers (Decimal/int/float) -> scale
    try:
        return float(v) * factor
    except Exception:
        return v


def allocate_monthly_totals(payload: MonthlyTotalsIn, include_data: bool = False) -> MonthlyTotalsOut:
    dbs = get_session()
    results: list[MonthlyAllocationResult] = []
    overall_rows_considered = 0
    overall_rows_written = 0
    overall_baseline_sum = 0.0
    months_with_allocation = 0

    try:
        requested_months = set(payload.month_totals.keys())  # ints 1..12

        # 1) Allocate for all months that WERE provided (scale to requested totals)
        for month, requested_total in sorted(payload.month_totals.items(), key=lambda kv: kv[0]):
            rows = dbs.query(ProjectionEstimate).filter(
                ProjectionEstimate.month == month).all()
            rows_considered = len(rows)
            overall_rows_considered += rows_considered

            baseline_sum = sum(float(r.est_total_sales or 0) for r in rows)
            overall_baseline_sum += baseline_sum

            if rows_considered == 0 or baseline_sum <= 0:
                results.append(MonthlyAllocationResult(
                    month=month,
                    rows_considered=rows_considered,
                    rows_written=0,
                    baseline_sum=float(baseline_sum),
                    applied_factor=0.0,
                    skipped_zero_baseline=rows_considered
                ))
                continue

            factor = float(requested_total) / float(baseline_sum)
            months_with_allocation += 1

            rows_written = 0
            for r in rows:
                vals = {}
                for col in ProjectionEstimateAdjusted.__table__.columns.keys():
                    if col in DONT_TOUCH:
                        continue
                    if hasattr(r, col):
                        v = getattr(r, col)
                        vals[col] = _scale_value(
                            col, v, factor) if col in NUMERIC_COLS else v

                ins = pg_insert(ProjectionEstimateAdjusted).values(**vals)
                stmt = ins.on_conflict_do_update(
                    index_elements=['branch_id', 'month'],
                    set_={k: getattr(ins.excluded, k) for k in vals.keys(
                    ) if k not in ('branch_id', 'month')}
                )
                dbs.execute(stmt)
                rows_written += 1

            overall_rows_written += rows_written
            results.append(MonthlyAllocationResult(
                month=month,
                rows_considered=rows_considered,
                rows_written=rows_written,
                baseline_sum=float(baseline_sum),
                applied_factor=factor,
                skipped_zero_baseline=0
            ))

        # 2) For months NOT provided: recompute from baseline (factor=1), i.e., refresh adjusted
        missing_months = set(range(1, 13)) - requested_months
        for month in sorted(missing_months):
            # we don’t “allocate” a target — we just reset adjusted to baseline
            rows_written = _upsert_from_baseline_for_month(dbs, month)
            # For reporting, we’ll also gather counts quickly:
            rows_considered = dbs.query(ProjectionEstimate).filter(
                ProjectionEstimate.month == month).count()
            overall_rows_considered += rows_considered
            baseline_sum = dbs.query(ProjectionEstimate)\
                              .with_entities(func.coalesce(func.sum(ProjectionEstimate.est_total_sales), 0.0))\
                              .filter(ProjectionEstimate.month == month).scalar() or 0.0
            overall_baseline_sum += float(baseline_sum)
            results.append(MonthlyAllocationResult(
                month=month,
                rows_considered=rows_considered,
                rows_written=rows_written,
                baseline_sum=float(baseline_sum),
                applied_factor=1.0,
                skipped_zero_baseline=0
            ))

        dbs.commit()

        out = MonthlyTotalsOut(
            results=sorted(results, key=lambda r: r.month),
            overall_rows_considered=overall_rows_considered,
            overall_rows_written=overall_rows_written,
            overall_baseline_sum=overall_baseline_sum,
            months_requested=len(requested_months),
            months_with_allocation=months_with_allocation,
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
