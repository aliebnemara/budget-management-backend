# services/allocation_service.py
from sqlalchemy.dialects.postgresql import insert as pg_insert
from src.core.db import get_session, close_session
from src.db.dbtables import ProjectionEstimate
from src.models.projection_est_adjust import AllocateGrandTotalIn, AllocateGrandTotalOut
from src.services.grouped_payload import build_grouped_payload
from src.db.projection_allocation import ProjectionEstimateAdjusted

DONT_TOUCH = {"id", "created_at", "updated_at"}

# We will ONLY scale sales/amount fields. We do NOT scale averages, percentages, or transactions.
SCALE_COLS = {
    # totals/amounts:
    "est_total_sales", "est_total_discount", "est_vat", "est_net_sales",
    # channel sales:
    "est_dine_sales", "est_delivery_sales", "est_takeway_sales",
    "est_drivethru_sales", "est_catering_sales",
}

# numeric fields to copy as-is (explicitly listed for clarity; others will also copy as-is)
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
    "est_customer_count",
    # keys/identifiers
    "branch_id", "month",
}


def allocate_grand_total(payload: AllocateGrandTotalIn, include_data: bool = False) -> AllocateGrandTotalOut:
    dbs = get_session()
    try:
        rows = dbs.query(ProjectionEstimate).all()
        if not rows:
            return AllocateGrandTotalOut(
                grand_total_estimated_sales=float(payload.grand_total_estimated_sales),
                rows_considered=0, rows_written=0,
                baseline_sum=0.0, applied_factor=0.0, skipped_zero_baseline=0,
                data=[] if include_data else None
            )

        baseline_sum = sum(float(r.est_total_sales or 0) for r in rows)
        if baseline_sum <= 0:
            return AllocateGrandTotalOut(
                grand_total_estimated_sales=float(payload.grand_total_estimated_sales),
                rows_considered=len(rows), rows_written=0,
                baseline_sum=0.0, applied_factor=0.0, skipped_zero_baseline=len(rows),
                data=[] if include_data else None
            )

        factor = float(payload.grand_total_estimated_sales) / float(baseline_sum)

        # bulk upsert adjusted rows
        written = 0
        for r in rows:
            vals = {}
            # copy branch_id & month first (required for upsert key)
            if hasattr(r, "branch_id"):
                vals["branch_id"] = r.branch_id
            if hasattr(r, "month"):
                vals["month"] = r.month

            for col in ProjectionEstimateAdjusted.__table__.columns.keys():
                if col in DONT_TOUCH or col in {"branch_id", "month"}:
                    continue

                if hasattr(r, col):
                    v = getattr(r, col)

                    if col in SCALE_COLS:
                        # scale amounts by factor
                        vals[col] = None if v is None else float(v) * factor
                    else:
                        # copy as-is for averages, percentages, transactions, counts, etc.
                        vals[col] = float(v) if isinstance(v, (int, float)) else v

            ins = pg_insert(ProjectionEstimateAdjusted).values(**vals)
            stmt = ins.on_conflict_do_update(
                index_elements=['branch_id', 'month'],
                set_={k: getattr(ins.excluded, k) for k in vals.keys() if k not in ('branch_id', 'month')}
            )
            dbs.execute(stmt)
            written += 1

        dbs.commit()

        result = AllocateGrandTotalOut(
            grand_total_estimated_sales=float(payload.grand_total_estimated_sales),
            rows_considered=len(rows),
            rows_written=written,
            baseline_sum=baseline_sum,
            applied_factor=factor,
            skipped_zero_baseline=0,
            data=None,
        )

        if include_data:
            # include baseline so the consumer sees actuals + adjusted together
            result.data = build_grouped_payload(include_baseline=True)

        return result
    except Exception:
        dbs.rollback()
        raise
    finally:
        close_session(dbs)
