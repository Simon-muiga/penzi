from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
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


@router.get("/users", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    return db.query(models.User).all()


@router.get("/messages", response_model=List[MessageResponse])
def get_messages(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    return db.query(models.Message).all()


@router.get("/matches", response_model=List[MatchResponse])
def get_matches(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    return db.query(models.Match).all()


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
        "completed_users": db.query(models.User).filter(models.User.registration_stage == "complete").count(),
        "inbound_messages": db.query(models.Message).filter(models.Message.direction == "inbound").count(),
        "outbound_messages": db.query(models.Message).filter(models.Message.direction == "outbound").count(),
    }