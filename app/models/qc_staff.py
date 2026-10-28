
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


class QCStaff(Base):
    __tablename__ = "qc_staff"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=False)

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    category = relationship("Category")
