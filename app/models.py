import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    gibney_email = Column(String, nullable=True)  # Encrypted
    gibney_password = Column(String, nullable=True)  # Encrypted
    calendar_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    bookings = relationship("Booking", back_populates="user")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(String, primary_key=True)  # From Gibney (e.g., "a27Pb...")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "R-490015"
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    studio = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    record_url = Column(String, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="bookings") 