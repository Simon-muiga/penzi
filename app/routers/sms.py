from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SmsRequest, SmsResponse
from app.services.sms_handler import handle_message, save_message

router = APIRouter(tags=["SMS"])


@router.get("/")
def read_root():
    return {"message": "Welcome to Penzi Dating Service API"}


@router.post("/sms", response_model=SmsResponse)
def receive_sms(payload: SmsRequest, db: Session = Depends(get_db)):
    sender = payload.sender.strip()
    message = payload.message.strip()

    save_message(db, sender, "22141", message, "inbound")
    response = handle_message(sender, message, db)
    save_message(db, "22141", sender, response, "outbound")

    return {"response": response}