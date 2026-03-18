from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import engine, get_db
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to Penzi Dating Service API"}

@app.post("/sms")
def receive_sms(payload: dict, db: Session = Depends(get_db)):
    sender = payload.get("sender")
    message = payload.get("message")

    new_message = models.Message(
        sender=sender,
        receiver="22141",
        message=message,
        direction="inbound"
    )
    db.add(new_message)
    db.commit()

    return {"response": f"Received message from {sender}"}