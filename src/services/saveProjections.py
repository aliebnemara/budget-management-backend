from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func
from src.core.db import get_session, close_session
from src.db.dbtables import ProjectionEstimate, ProjectionInput
from src.db.projection_allocation import ProjectionEstimateAdjusted

def upsert_projection_input(payload: dict):
    dbs = get_session()
    try:
        # Keep only valid columns for this table
        table_cols = {c.name for c in ProjectionInput.__table__.columns}
        values = {k: v for k, v in payload.items() if k in table_cols}

        if not values:
            raise ValueError("No valid columns in payload for ProjectionInput")

        ins = pg_insert(ProjectionInput).values(**values)

        # Columns we allow to update (exclude key/auto columns)
        dont_touch = {"id", "created_at", "updated_at", "branch_id", "month"}
        update_map = {
            k: getattr(ins.excluded, k)
            for k in values.keys()
            if k not in dont_touch
        }

        stmt = ins.on_conflict_do_update(
            index_elements=[ProjectionInput.branch_id, ProjectionInput.month],
            set_={**update_map, "updated_at": func.now()},
        )

        dbs.execute(stmt)
        dbs.commit()
    except Exception:
        dbs.rollback()
        raise
    finally:
        close_session(dbs)


REQUIRED = {"branch_id", "month"}

def upsert_projection_estimate(payload: dict):
    """Upsert a single (branch_id, month) estimates row."""
    dbs = get_session()
    try:
        table_cols = {c.name for c in ProjectionEstimate.__table__.columns}
        values = {k: v for k, v in payload.items() if k in table_cols}
        missing = REQUIRED - values.keys()
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(sorted(missing))}")

        # normalize month
        values["month"] = int(values["month"])
        if not 1 <= values["month"] <= 12:
            raise ValueError("month must be in 1..12")

        ins = pg_insert(ProjectionEstimate).values(**values)

        dont_touch = {"id", "created_at", "updated_at", "branch_id", "month"}
        update_map = {k: getattr(ins.excluded, k) for k in values if k not in dont_touch}

        stmt = ins.on_conflict_do_update(
            index_elements=[ProjectionEstimate.branch_id, ProjectionEstimate.month],
            set_={**update_map, "updated_at": func.now()},
        ).returning(ProjectionEstimate.id)

        result = dbs.execute(stmt).scalar_one()
        dbs.commit()
        return {"id": result}
    except Exception:
        dbs.rollback()
        raise
    finally:
        close_session(dbs)

DONT_TOUCH = {"id", "created_at", "updated_at", "branch_id", "month"}

def bulk_upsert_projection_estimate_adjusted(rows: list[dict]) -> int:
    """Bulk upsert adjusted estimates by (branch_id, month). Returns rows written."""
    if not rows:
        return 0

    # Keep only valid columns
    table_cols = {c.name for c in ProjectionEstimateAdjusted.__table__.columns}
    clean = [{k: v for k, v in r.items() if k in table_cols} for r in rows]

    dbs = get_session()
    try:
        ins = pg_insert(ProjectionEstimateAdjusted).values(clean)
        update_map = {k: getattr(ins.excluded, k) for k in clean[0].keys() if k not in DONT_TOUCH}
        stmt = ins.on_conflict_do_update(
            constraint="uq_projection_estimate_adjusted_branch_month",
            set_={**update_map, "updated_at": func.now()},
        )
        dbs.execute(stmt)
        dbs.commit()
        return len(clean)
    except Exception:
        dbs.rollback()
        raise
    finally:
        close_session(dbs)