
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String(150), nullable=False, index=True)

    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    manager_name = Column(String(150), nullable=False)
    address = Column(Text, nullable=False)

    delivery_area_id = Column(
        Integer, ForeignKey("delivery_areas.id"), nullable=False
    )

    status = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    category = relationship("Category", back_populates="stores")
    delivery_area = relationship("DeliveryArea", back_populates="stores")

    products = relationship("Product", back_populates="store")
    coupons = relationship("Coupon", back_populates="store")
