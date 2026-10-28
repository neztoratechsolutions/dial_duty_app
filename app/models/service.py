
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Boolean,
    DateTime,
)

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)

    # Required fields
    service_name = Column(String(150), nullable=False)
    service_type = Column(String(100), nullable=False)

    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=False)

    duration_minutes = Column(Integer, nullable=False)

    # Optional fields
    description = Column(Text, nullable=True)
    rating = Column(Numeric(3, 2), nullable=True)
    image_url = Column(String(500), nullable=True)

    # Default fields
    total_reviews = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
