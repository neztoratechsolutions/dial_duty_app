from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from app.database import Base


class ProductReview(Base):
    __tablename__ = "product_reviews"

    __table_args__ = (
        CheckConstraint(
            "star_rating >= 1 AND star_rating <= 5",
            name="check_review_star_rating",
        ),
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_product_review_user_product",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    star_rating = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )