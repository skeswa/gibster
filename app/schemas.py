from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID


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
