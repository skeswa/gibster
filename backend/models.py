import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

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
    last_sync_at = Column(DateTime, nullable=True)  # Track last sync time

    # Relationship
    bookings = relationship("Booking", back_populates="user")
    sync_jobs = relationship("SyncJob", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"

    def __str__(self):
        return f"<User {self.email}>"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True)  # From Gibney (e.g., "a27Pb...")
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name = Column(String, nullable=False)  # e.g., "R-490015"
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    studio = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    record_url = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="bookings")

    def __repr__(self):
        return f"<Booking {self.name} - {self.studio}>"

    def create_hash(self):
        """Create a hash of relevant booking fields for change detection"""
        import hashlib
        import json

        relevant_fields = {
            "name": self.name,
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
            "studio": self.studio,
            "location": self.location,
            "status": self.status,
            "price": float(getattr(self, "price", 0) or 0),
        }

        json_str = json.dumps(relevant_fields, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        String, nullable=False
    )  # 'pending', 'running', 'completed', 'failed'
    progress = Column(String, nullable=True)  # Progress message
    bookings_synced = Column(Numeric, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    triggered_manually = Column(Boolean, default=False)  # Track if sync was manual
    last_updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )  # Track last activity

    # Relationships
    user = relationship("User", back_populates="sync_jobs")
    logs = relationship(
        "SyncJobLog", back_populates="sync_job", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SyncJob {self.id} - {self.status}>"


class SyncJobLog(Base):
    __tablename__ = "sync_job_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_job_id = Column(
        UUID(as_uuid=True), ForeignKey("sync_jobs.id"), nullable=False, index=True
    )
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    level = Column(String, nullable=False)  # 'INFO', 'WARNING', 'ERROR', 'DEBUG'
    message = Column(Text, nullable=False)
    details = Column(
        JSON, nullable=True
    )  # Structured data like response times, URLs, etc.

    # Relationship
    sync_job = relationship("SyncJob", back_populates="logs")

    def __repr__(self):
        return f"<SyncJobLog {self.id} - {self.level}: {self.message[:50]}...>"
