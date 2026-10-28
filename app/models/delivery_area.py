from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class DeliveryArea(Base):
    __tablename__ = "delivery_areas"

    id = Column(Integer, primary_key=True, index=True)
    pincode = Column(String(10), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    status = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    stores = relationship("Store", back_populates="delivery_area")
    delivery_boys = relationship("DeliveryBoy", back_populates="area")
    category = relationship("Category")
