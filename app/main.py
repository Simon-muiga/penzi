from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
from app.routers import sms, admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Penzi Dating Service API",
    description="SMS-based dating service for Onfon Connect platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sms.router)
app.include_router(admin.router)