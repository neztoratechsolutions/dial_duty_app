
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Numeric, UniqueConstraint
)
from app.database import Base


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )
    code = Column(String(30), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint(
            "referred_user_id",
            name="uq_referrals_referred_user"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    referred_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    status = Column(String(20), default="pending", nullable=False)
    reward_amount = Column(Numeric(10, 2), default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    credited_at = Column(DateTime, nullable=True)
