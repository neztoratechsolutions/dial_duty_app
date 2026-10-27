from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)

from app.database import Base


class ServiceBooking(Base):
    __tablename__ = "service_bookings"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id"),
        nullable=False,
        index=True,
    )

    warranty_number = Column(String(100), nullable=True)

    issue_photo = Column(String(500), nullable=True)

    issue_description = Column(Text, nullable=False)

    booking_status = Column(
        String(30),
        default="Pending",
        nullable=False,
    )

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