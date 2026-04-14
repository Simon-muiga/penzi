from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app import models
from app.schemas import (
    AdminCreate, Token, UserResponse,
    MessageResponse, MatchResponse, StatsResponse
)
from app.services.auth import (
    hash_password, verify_password,
    create_access_token, get_current_admin
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/register")
def register_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    if len(admin_data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    if len(admin_data.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
    if db.query(models.Admin).filter(models.Admin.username == admin_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(models.Admin).filter(models.Admin.email == admin_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_admin = models.Admin(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=hash_password(admin_data.password)
    )
    db.add(new_admin)
    db.commit()
    return {"message": f"Admin {admin_data.username} created successfully"}


@router.post("/login", response_model=Token)
def login_admin(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    admin = db.query(models.Admin).filter(
        models.Admin.username == form_data.username
    ).first()

    if not admin or not verify_password(form_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    county: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    registration_stage: Optional[str] = Query(default=None),
    date_range: Optional[str] = Query(default=None),
):
    query = db.query(models.User)

    # Search by name or phone
    if search:
        query = query.filter(
            models.User.name.ilike(f"%{search}%") |
            models.User.phone_number.ilike(f"%{search}%")
        )

    # Filter by county
    if county:
        query = query.filter(models.User.county.ilike(f"%{county}%"))

    # Filter by gender
    if gender:
        query = query.filter(models.User.gender.ilike(f"%{gender}%"))

    # Filter by registration stage
    if registration_stage:
        if registration_stage == "complete":
            query = query.filter(models.User.registration_stage == "complete")
        elif registration_stage == "partial":
            query = query.filter(models.User.registration_stage != "complete")

    # Filter by date range
    if date_range:
        now = datetime.utcnow()
        if date_range == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.User.created_at >= start)
        elif date_range == "this_week":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.User.created_at >= start)
        elif date_range == "this_month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.User.created_at >= start)
        elif date_range == "last_month":
            first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end = first_this_month - timedelta(seconds=1)
            last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(
                models.User.created_at >= last_month_start,
                models.User.created_at <= last_month_end
            )

    query = query.order_by(models.User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    # Get all unique counties for the dropdown
    all_counties = db.query(models.User.county).distinct().all()
    counties = sorted([c[0] for c in all_counties if c[0]])

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "counties": counties,
        "data": users
    }


@router.get("/messages")
def get_messages(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    direction: Optional[str] = Query(default=None),
    date_range: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
):
    query = db.query(models.Message)

    if direction and direction in ["inbound", "outbound"]:
        query = query.filter(models.Message.direction == direction)

    if search:
        query = query.filter(
            models.Message.sender.ilike(f"%{search}%") |
            models.Message.receiver.ilike(f"%{search}%") |
            models.Message.message.ilike(f"%{search}%")
        )

    if date_range:
        now = datetime.utcnow()
        if date_range == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.Message.created_at >= start)
        elif date_range == "this_week":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.Message.created_at >= start)
        elif date_range == "this_month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.Message.created_at >= start)
        elif date_range == "last_month":
            first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end = first_this_month - timedelta(seconds=1)
            last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(
                models.Message.created_at >= last_month_start,
                models.Message.created_at <= last_month_end
            )

    query = query.order_by(models.Message.created_at.desc())
    total = query.count()
    messages = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": messages
    }


@router.get("/matches")
def get_matches(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    date_range: Optional[str] = Query(default=None),
):
    query = db.query(models.Match)

    if status and status in ["pending", "accepted"]:
        query = query.filter(models.Match.status == status)

    if date_range:
        now = datetime.utcnow()
        if date_range == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.Match.created_at >= start)
        elif date_range == "this_week":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.Match.created_at >= start)
        elif date_range == "this_month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.Match.created_at >= start)

    total = query.count()
    matches_raw = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for match in matches_raw:
        requester = db.query(models.User).filter(
            models.User.phone_number == match.requester_phone
        ).first()
        matched = db.query(models.User).filter(
            models.User.phone_number == match.matched_phone
        ).first()
        result.append({
            "id": match.id,
            "requester_phone": match.requester_phone,
            "requester_name": requester.name if requester else "Unknown",
            "requester_age": requester.age if requester else "N/A",
            "requester_town": requester.town if requester else "N/A",
            "matched_phone": match.matched_phone,
            "matched_name": matched.name if matched else "Unknown",
            "matched_age": matched.age if matched else "N/A",
            "matched_town": matched.town if matched else "N/A",
            "status": match.status,
            "created_at": match.created_at
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": result
    }


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    return {
        "total_users": db.query(models.User).count(),
        "total_messages": db.query(models.Message).count(),
        "total_matches": db.query(models.Match).count(),
        "total_admins": db.query(models.Admin).count(),
        "completed_users": db.query(models.User).filter(
            models.User.registration_stage == "complete"
        ).count(),
        "inbound_messages": db.query(models.Message).filter(
            models.Message.direction == "inbound"
        ).count(),
        "outbound_messages": db.query(models.Message).filter(
            models.Message.direction == "outbound"
        ).count(),
    }