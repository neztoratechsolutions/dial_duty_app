
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    mobile_number = Column(String(20), unique=True, nullable=False, index=True)
    address = Column(Text, nullable=True)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    referral_code = Column(String(30), unique=True, nullable=False, index=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    role = relationship("Role", back_populates="users")

    referrer = relationship(
        "User",
        remote_side=[id],
        back_populates="referrals"
    )

    referrals = relationship(
        "User",
        back_populates="referrer"
    )
