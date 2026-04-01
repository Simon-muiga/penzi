from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import engine, get_db
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from app import models

models.Base.metadata.create_all(bind=engine)

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")      
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000",
                   "http://localhost:8001",
                   "http://127.0.0.1:8001",
    ],
    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AdminCreate(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = db.query(models.Admin).filter(
        models.Admin.username == username
    ).first()

    if admin is None:
        raise credentials_exception
    return admin


@app.get("/")
def read_root():
    return {"message": "Penzi Admin API"}


@app.post("/admin/register")
def register_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Admin).filter(
        models.Admin.username == admin_data.username
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    existing_email = db.query(models.Admin).filter(
        models.Admin.email == admin_data.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    new_admin = models.Admin(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=hash_password(admin_data.password)
    )
    db.add(new_admin)
    db.commit()

    return {"message": f"Admin {admin_data.username} created successfully"}


@app.post("/admin/login", response_model=Token)
def login_admin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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


@app.get("/admin/users")
def get_users(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    users = db.query(models.User).all()
    return users


@app.get("/admin/messages")
def get_messages(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    messages = db.query(models.Message).all()
    return messages


@app.get("/admin/matches")
def get_matches(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    matches = db.query(models.Match).all()
    return matches


@app.get("/admin/stats")
def get_stats(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    total_users = db.query(models.User).count()
    total_messages = db.query(models.Message).count()
    total_matches = db.query(models.Match).count()
    total_admins = db.query(models.Admin).count()
    completed_users = db.query(models.User).filter(
        models.User.registration_stage == "complete"
    ).count()
    inbound_messages = db.query(models.Message).filter(
        models.Message.direction == "inbound"
    ).count()
    outbound_messages = db.query(models.Message).filter(
        models.Message.direction == "outbound"
    ).count()

    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "total_matches": total_matches,
        "total_admins": total_admins,
        "completed_users": completed_users,
        "inbound_messages": inbound_messages,
        "outbound_messages": outbound_messages
    }