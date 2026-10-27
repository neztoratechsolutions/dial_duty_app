
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Numeric, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_product_price"),
        CheckConstraint(
            "stock_quantity >= 0",
            name="check_product_stock"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(150), nullable=False, index=True)

    store_id = Column(
        Integer, ForeignKey("stores.id"), nullable=False
    )
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=False
    )

    brand = Column(String(100), nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    stock_quantity = Column(Integer, nullable=False, default=0)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")

    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    questions_answers = relationship(
        "ProductQA",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    images = relationship(
    "ProductImage",
    back_populates="product",
    cascade="all, delete-orphan"
)
