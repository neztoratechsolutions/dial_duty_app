
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class Reel(Base):
    __tablename__ = "reels"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    # Stores whether the uploaded file is an image or video
    media_type = Column(String(20), nullable=False)
    media_url = Column(String(500), nullable=False)

    # New reels are active by default
    status = Column(String(20), default="active", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )