
from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ProductQA(Base):
    __tablename__ = "product_qa"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    question_en = Column(Text, nullable=False)
    answer_en = Column(Text, nullable=False)

    question_ta = Column(Text, nullable=True)
    answer_ta = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    product = relationship("Product", back_populates="questions_answers")
