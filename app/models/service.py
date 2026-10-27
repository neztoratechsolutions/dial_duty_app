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

    service_name = Column(String(150), nullable=False)
    service_type = Column(String(100), nullable=True)

    description = Column(Text, nullable=False)

    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=True)

    rating = Column(Numeric(3, 2), nullable=True)
    total_reviews = Column(Integer, default=0, nullable=False)

    duration_minutes = Column(Integer, nullable=False)

    image_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

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