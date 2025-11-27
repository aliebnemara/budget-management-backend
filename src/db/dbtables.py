from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, func, UniqueConstraint, Index, Date, Text, Float, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
Base = declarative_base()

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for many-to-many relationship between users and brands
user_brands = Table(
    'user_brands',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('brand_id', Integer, ForeignKey('brand.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for many-to-many relationship between users and branches
user_branches = Table(
    'user_branches',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('branch_id', Integer, ForeignKey('branch.id', ondelete='CASCADE'), primary_key=True)
)


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    permissions = Column(JSONB, nullable=False, default={})  # Store permissions as JSON
    
    # Many-to-many relationship with users
    users = relationship('User', secondary=user_roles, back_populates='roles')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Many-to-many relationships
    roles = relationship('Role', secondary=user_roles, back_populates='users')
    brands = relationship('Brand', secondary=user_brands)
    branches = relationship('Branch', secondary=user_branches)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)



class Brand(Base):
    __tablename__ = "brand"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Audit tracking fields
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    edited_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    edited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # one-to-many
    branches = relationship(
        "Branch",
        back_populates="brand",   # <-- must match attribute name below
        passive_deletes=False     # no cascade delete
    )
    
    # Relationships for audit tracking
    added_by_user = relationship("User", foreign_keys=[added_by], lazy="joined")
    edited_by_user = relationship("User", foreign_keys=[edited_by], lazy="joined")
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], lazy="joined")


class Branch(Base):
    __tablename__ = "branch"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Audit tracking fields
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    edited_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    edited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Foreign key to Brand (single definition with index and restrict delete)
    brand_id = Column(Integer, ForeignKey(
        "brand.id", ondelete="RESTRICT"), index=True, nullable=False)

    # many-to-one
    brand = relationship(       # <-- this must exist and be named "brand"
        "Brand",
        back_populates="branches"
    )
    
    # Relationships for audit tracking
    added_by_user = relationship("User", foreign_keys=[added_by], lazy="joined")
    edited_by_user = relationship("User", foreign_keys=[edited_by], lazy="joined")
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], lazy="joined")


class ProjectionInput(Base):
    __tablename__ = "projection_input"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branch.id"), nullable=False)
    # year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # % deltas and projected values (nullable so you can fill as user provides)
    dining_sales_pct = Column(Numeric(8, 4))   # DINING SALES +/- IN %
    projected_dinin_avg_check = Column(Numeric(12, 4))
    projected_avg_per_cover = Column(Numeric(12, 4))
    projected_guest_count_new = Column(Numeric(12, 4))

    delivery_sales_pct = Column(Numeric(8, 4))
    projected_delivery_avg_check = Column(Numeric(12, 4))

    takeaway_sales_pct = Column(Numeric(8, 4))
    projected_takeaway_avg_check = Column(Numeric(12, 4))

    drivethru_sales_pct = Column(Numeric(8, 4))
    projected_drivethru_avg_check = Column(Numeric(12, 4))

    catering_trans_pct = Column(Numeric(8, 4))
    projected_catering_avg_check = Column(Numeric(12, 4))

    projected_discount_pct = Column(Numeric(8, 4))
    marketing_activities_pct = Column(
        Numeric(8, 4))   # "Marketing Activities %"

    projected_delivery_sales_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_delivery_trans_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_dinein_sales_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_dinein_trans_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_takeaway_sales_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_takeaway_trans_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_drivethru_sales_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_drivethru_trans_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_catering_sales_new = Column(Numeric(14, 4))  # NEW OPENING
    projected_catering_trans_new = Column(Numeric(14, 4))  # NEW OPENING

    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(
    ), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("branch_id", "month",
                         name="uq_projection_input_period"),
        Index("ix_projection_period", "branch_id", "month"),
    )


class BudgetRuntimeState(Base):
    __tablename__ = "budget_runtime_state"

    id = Column(Integer, primary_key=True, default=1)

    # inputs as scalar columns
    compare_year = Column(Integer, nullable=False)
    ramadan_cy = Column(Date, nullable=False)
    ramadan_by = Column(Date, nullable=False)
    ramadan_daycount_cy = Column(Integer, nullable=False)
    ramadan_daycount_by = Column(Integer, nullable=False)
    muharram_cy = Column(Date, nullable=False)
    muharram_by = Column(Date, nullable=False)
    muharram_daycount_cy = Column(Integer, nullable=False)
    muharram_daycount_by = Column(Integer, nullable=False)
    eid2_cy = Column(Date, nullable=False)
    eid2_by = Column(Date, nullable=False)

    # input_hash = Column(Text, nullable=False)         # fingerprint of inputs
    # cached result (no projected fields)
    result_json = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(
    ), onupdate=func.now(), nullable=False)

class ProjectionEstimate(Base):
    __tablename__ = "projection_estimates"
    id = Column(Integer, primary_key=True, autoincrement=True)

    branch_id = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1..12

    # Estimated Dine-in
    est_dine_sales = Column(Float)
    est_dine_trans = Column(Float)
    est_customer_count = Column(Float)
    est_dine_avg_check = Column(Float)
    est_avg_per_cover = Column(Float)

    # Estimated Delivery
    est_delivery_sales = Column(Float)
    est_delivery_trans = Column(Float)
    est_delivery_avg_check = Column(Float)

    # Estimated Takeaway
    est_takeway_sales = Column(Float)
    est_takeway_trans = Column(Float)
    est_takeway_avg_check = Column(Float)

    # Estimated Drive-thru
    est_drivethru_sales = Column(Float)
    est_drivethru_trans = Column(Float)
    est_drivethru_avg_check = Column(Float)

    # Estimated Catering
    est_catering_sales = Column(Float)
    est_catering_trans = Column(Float)
    est_catering_avg_check = Column(Float)

    # Totals/rollups
    est_total_sales = Column(Float)
    est_total_trans = Column(Float)
    est_total_avg = Column(Float)
    est_total_discount = Column(Float)
    est_discount_pct = Column(Float)
    est_vat = Column(Float)
    est_net_sales = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("branch_id", "month", name="uq_projection_estimates_branch_month"),
    )


class BudgetEffectCalculationsV2(Base):
    """
    V2 table to store pre-calculated weekend and Islamic calendar effects.
    Calculate once, view many times for 10-20x faster page loads.
    """
    __tablename__ = "budget_effect_calculations_v2"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey("branch.id"), nullable=False, index=True)
    budget_year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)  # 1..12
    
    # Weekend/Weekday Effect - Final percentages
    weekday_effect_pct = Column(Numeric(10, 4))  # e.g., +5.23% or -3.45%
    
    # Islamic Calendar Effects - Final percentages
    ramadan_eid_pct = Column(Numeric(10, 4))     # Ramadan/Eid combined effect
    muharram_pct = Column(Numeric(10, 4))        # Muharram effect
    eid2_pct = Column(Numeric(10, 4))            # Eid Al-Adha effect
    
    # Detailed breakdowns stored as JSON
    weekday_breakdown = Column(JSONB)     # Daily weekday pattern + monthly distribution
    ramadan_breakdown = Column(JSONB)     # 6-month daily Ramadan data
    muharram_breakdown = Column(JSONB)    # Daily Muharram data
    eid2_breakdown = Column(JSONB)        # Daily Eid Al-Adha data
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    calculated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    restaurant = relationship("Branch")
    calculated_by_user = relationship("User", foreign_keys=[calculated_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("restaurant_id", "budget_year", "month", 
                        name="uq_budget_effect_calc_v2_rest_year_month"),
        Index("idx_budget_effect_v2_rest_year", "restaurant_id", "budget_year"),
    )
