from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


class DeliveryBoy(Base):
    __tablename__ = "delivery_boys"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)

    area_id = Column(
        Integer,
        ForeignKey("delivery_areas.id"),
        nullable=False,
    )

    # Category ID from categories table
    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )

    status = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    area = relationship(
        "DeliveryArea",
        back_populates="delivery_boys",
    )

    category = relationship("Category")