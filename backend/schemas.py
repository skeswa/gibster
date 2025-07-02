from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserCredentials(BaseModel):
    gibney_email: str
    gibney_password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    calendar_uuid: UUID
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Booking schemas
class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    start_time: datetime
    end_time: datetime
    studio: str
    location: str
    status: str
    price: Optional[float]
    record_url: str
    last_seen: datetime


class CalendarUrl(BaseModel):
    calendar_url: str
    calendar_uuid: UUID


# Sync Job schemas
class SyncJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    progress: Optional[str]
    bookings_synced: int
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    triggered_manually: bool


class SyncStartResponse(BaseModel):
    job_id: UUID
    message: str
    status: str


class SyncStatusResponse(BaseModel):
    job: SyncJobResponse
    last_sync_at: Optional[datetime]


# Sync Job Log schemas
class SyncJobLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sync_job_id: UUID
    timestamp: datetime
    level: str
    message: str
    details: Optional[Dict[str, Any]]


class SyncJobLogsResponse(BaseModel):
    logs: List[SyncJobLogResponse]
    total: int
    page: int
    limit: int
