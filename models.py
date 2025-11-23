from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("Creator", back_populates="user", uselist=False)


class Creator(Base):
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    display_name = Column(String(150))
    nickname = Column(String(100))
    bio = Column(Text)
    instagram_url = Column(String(255))
    spotify_url = Column(String(255))
    other_links = Column(JSON, default=list)
    barcode_slug = Column(String(64), unique=True, index=True)
    barcode_image_url = Column(String(512))
    profile_image_url = Column(String(512))
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="creator")
    media_items = relationship("Media", back_populates="creator", cascade="all,delete")


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(
        Integer, ForeignKey("creators.id", ondelete="CASCADE"), nullable=False
    )
    media_type = Column(Enum("image", "audio", "video", name="media_type"))
    url = Column(String(512))
    title = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("Creator", back_populates="media_items")


class EmailCapture(Base):
    __tablename__ = "email_captures"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

