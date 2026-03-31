from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(15), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    county = Column(String(50), nullable=False)
    town = Column(String(50), nullable=False)
    education = Column(String(50), nullable=True)
    profession = Column(String(50), nullable=True)
    marital_status = Column(String(20), nullable=True)
    religion = Column(String(30), nullable=True)
    ethnicity = Column(String(50), nullable=True)
    self_description = Column(Text, nullable=True)
    registration_stage = Column(String(100), default="basic")
    created_at = Column(DateTime, server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String(20), nullable=False)
    receiver = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    direction = Column(String(10), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    requester_phone = Column(String(20), nullable=False)
    matched_phone = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())