from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Numeric, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    __table_args__ = (
        CheckConstraint("discount >= 0", name="check_coupon_discount"),
        CheckConstraint(
            "discount_type IN ('percentage', 'fixed')",
            name="check_coupon_discount_type"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)

    discount = Column(Numeric(12, 2), nullable=False)
    discount_type = Column(
        String(20), nullable=False, default="percentage"
    )

    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    store_id = Column(
        Integer, ForeignKey("stores.id"), nullable=True
    )

    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=False
    )

    status = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    store = relationship("Store", back_populates="coupons")
    category = relationship("Category")
