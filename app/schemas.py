from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── SMS SCHEMAS ──

class SmsRequest(BaseModel):
    sender: str
    message: str

class SmsResponse(BaseModel):
    response: str


# ── USER SCHEMAS ──

class UserResponse(BaseModel):
    id: int
    phone_number: str
    name: str
    age: int
    gender: str
    county: str
    town: str
    education: Optional[str] = None
    profession: Optional[str] = None
    marital_status: Optional[str] = None
    religion: Optional[str] = None
    ethnicity: Optional[str] = None
    self_description: Optional[str] = None
    registration_stage: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── MESSAGE SCHEMAS ──

class MessageResponse(BaseModel):
    id: int
    sender: str
    receiver: str
    message: str
    direction: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── MATCH SCHEMAS ──

class MatchResponse(BaseModel):
    id: int
    requester_phone: str
    matched_phone: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── ADMIN SCHEMAS ──

class AdminCreate(BaseModel):
    username: str
    email: str
    password: str

class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# ── STATS SCHEMA ──

class StatsResponse(BaseModel):
    total_users: int
    total_messages: int
    total_matches: int
    total_admins: int
    completed_users: int
    inbound_messages: int
    outbound_messages: int