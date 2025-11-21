from sqlalchemy import Column, Integer, SmallInteger, BigInteger, DateTime, UniqueConstraint, func, Numeric
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

NUM = lambda: Numeric(18, 4)
PCT = lambda: Numeric(9, 4)

class ProjectionEstimateAdjusted(Base):
    __tablename__ = "projection_estimate_adjusted"

    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(BigInteger, nullable=False)
    month = Column(SmallInteger, nullable=False)

    est_dine_sales = Column(NUM())
    est_dine_trans = Column(NUM())
    est_customer_count = Column(NUM())
    est_dine_avg_check = Column(NUM())
    est_avg_per_cover = Column(NUM())

    est_delivery_sales = Column(NUM())
    est_delivery_trans = Column(NUM())
    est_delivery_avg_check = Column(NUM())

    est_takeway_sales = Column(NUM())
    est_takeway_trans = Column(NUM())
    est_takeway_avg_check = Column(NUM())

    est_drivethru_sales = Column(NUM())
    est_drivethru_trans = Column(NUM())
    est_drivethru_avg_check = Column(NUM())

    est_catering_sales = Column(NUM())
    est_catering_trans = Column(NUM())
    est_catering_avg_check = Column(NUM())

    est_total_sales = Column(NUM())
    est_total_trans = Column(NUM())
    est_total_avg = Column(NUM())
    est_total_discount = Column(NUM())
    est_discount_pct = Column(PCT())
    est_vat = Column(NUM())
    est_net_sales = Column(NUM())

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("branch_id", "month", name="uq_projection_estimate_adjusted_branch_month"),
    )
