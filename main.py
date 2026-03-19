from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db
import models
import re

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["htttp://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_phone_number(text: str) -> bool:
    pattern = r'^(\+254|0)[17]\d{8}$'
    return bool(re.match(pattern, text.strip()))


def save_message(db: Session, sender: str, receiver: str, message: str, direction: str):
    new_message = models.Message(
        sender=sender,
        receiver=receiver,
        message=message,
        direction=direction
    )
    db.add(new_message)
    db.commit()


@app.get("/")
def read_root():
    return {"message": "Welcome to Penzi Dating Service API"}


@app.post("/sms")
def receive_sms(payload: dict, db: Session = Depends(get_db)):
    sender = payload.get("sender", "").strip()
    message = payload.get("message", "").strip()

    save_message(db, sender, "22141", message, "inbound")

    response = handle_message(sender, message, db)

    save_message(db, "22141", sender, response, "outbound")

    return {"response": response}


def handle_message(sender: str, message: str, db: Session) -> str:

    # STEP 1: PENZI - Service activation
    if message.upper() == "PENZI":
        return (
            "Welcome to our dating service with potential dating partners! "
            "To register SMS start#name#age#gender#county#town to 22141. "
            "E.g., start#Nickson#22#Male#Nairobi#Kitengela"
        )

    # STEP 2: start#... - Basic registration
    if message.lower().startswith("start#"):
        return handle_registration(sender, message, db)

    # STEP 3: details#... - Extra details
    if message.lower().startswith("details#"):
        return handle_details(sender, message, db)

    # STEP 4: MYSELF ... - Self description
    if message.upper().startswith("MYSELF"):
        return handle_self_description(sender, message, db)

    # STEP 5: match#... - Search for matches
    if message.lower().startswith("match#"):
        return handle_matching(sender, message, db)

    # STEP 6: NEXT - Get more matches
    if message.upper() == "NEXT":
        return handle_next(sender, db)

    # STEP 7: DESCRIBE 07xx - Get self description
    if message.upper().startswith("DESCRIBE"):
        return handle_describe(sender, message, db)

    # STEP 8: YES - Confirm interest
    if message.upper() == "YES":
        return handle_yes(sender, db)

    # STEP 9: Phone number - Get full profile
    if is_phone_number(message):
        return handle_profile_request(sender, message, db)

    return "Invalid command. SMS PENZI to 22141 to get started."


def handle_registration(sender: str, message: str, db: Session) -> str:
    parts = message.split("#")
    if len(parts) != 6:
        return "Invalid format. SMS start#name#age#gender#county#town to 22141."

    _, name, age, gender, county, town = parts

    if not age.isdigit():
        return "Invalid age. Please enter a number for age."

    existing_user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if existing_user:
        return f"You are already registered, {existing_user.name}. SMS match#ageRange#town to find a partner."

    new_user = models.User(
        phone_number=sender,
        name=name.strip(),
        age=int(age),
        gender=gender.strip(),
        county=county.strip(),
        town=town.strip(),
        registration_stage="basic"
    )
    db.add(new_user)
    db.commit()

    return (
        f"Your profile has been created successfully {name}. "
        "SMS details#levelOfEducation#profession#maritalStatus#religion#ethnicity to 22141. "
        "E.g. details#degree#engineer#single#christian#kikuyu"
    )


def handle_details(sender: str, message: str, db: Session) -> str:
    parts = message.split("#")
    if len(parts) != 6:
        return "Invalid format. SMS details#education#profession#maritalStatus#religion#ethnicity to 22141."

    _, education, profession, marital_status, religion, ethnicity = parts

    user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if not user:
        return "You are not registered. SMS PENZI to 22141 to get started."

    user.education = education.strip()
    user.profession = profession.strip()
    user.marital_status = marital_status.strip()
    user.religion = religion.strip()
    user.ethnicity = ethnicity.strip()
    user.registration_stage = "details"
    db.commit()

    return (
        "This is the last stage of registration. "
        "SMS a brief description of yourself to 22141 starting with the word MYSELF. "
        "E.g., MYSELF tall, dark and funny"
    )


def handle_self_description(sender: str, message: str, db: Session) -> str:
    description = message[6:].strip()

    if not description:
        return "Please provide a description after MYSELF. E.g., MYSELF tall, dark and funny"

    user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if not user:
        return "You are not registered. SMS PENZI to 22141 to get started."

    user.self_description = description
    user.registration_stage = "complete"
    db.commit()

    return (
        "You are now fully registered for dating. "
        "To search for a partner, SMS match#ageRange#town to 22141. "
        "E.g., match#20-25#Nairobi"
    )


def handle_matching(sender: str, message: str, db: Session) -> str:
    parts = message.split("#")
    if len(parts) != 3:
        return "Invalid format. SMS match#ageRange#town to 22141. E.g., match#20-25#Nairobi"

    _, age_range, town = parts

    user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if not user:
        return "You are not registered. SMS PENZI to 22141 to get started."

    age_parts = age_range.split("-")
    if len(age_parts) != 2 or not age_parts[0].isdigit() or not age_parts[1].isdigit():
        return "Invalid age range. Use format like 20-25."

    min_age = int(age_parts[0])
    max_age = int(age_parts[1])

    opposite_gender = "Female" if user.gender.lower() in ["male", "m"] else "Male"

    matches = db.query(models.User).filter(
        models.User.gender.ilike(f"%{opposite_gender}%"),
        models.User.age >= min_age,
        models.User.age <= max_age,
        models.User.town.ilike(f"%{town.strip()}%"),
        models.User.phone_number != sender
    ).all()

    if not matches:
        return f"Sorry, no matches found for age {age_range} in {town}. Try a different age range or town."

    user.registration_stage = f"matching_{town}_{age_range}_0"
    db.commit()

    total = len(matches)
    first_three = matches[:3]

    response = f"We have {total} {'ladies' if opposite_gender == 'Female' else 'men'} who match your choice! We will send you details of 3 of them shortly.\n"
    for match in first_three:
        response += f"{match.name} aged {match.age}, {match.phone_number}.\n"

    if total > 3:
        response += f"Send NEXT to 22141 to receive details of the remaining {total - 3} matches."

    return response.strip()


def handle_next(sender: str, db: Session) -> str:
    user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if not user or not user.registration_stage.startswith("matching_"):
        return "You have no active search. SMS match#ageRange#town to 22141 to search."

    parts = user.registration_stage.split("_")
    town = parts[1]
    age_range = parts[2]
    offset = int(parts[3]) + 3

    age_parts = age_range.split("-")
    min_age = int(age_parts[0])
    max_age = int(age_parts[1])

    opposite_gender = "Female" if user.gender.lower() in ["male", "m"] else "Male"

    matches = db.query(models.User).filter(
        models.User.gender.ilike(f"%{opposite_gender}%"),
        models.User.age >= min_age,
        models.User.age <= max_age,
        models.User.town.ilike(f"%{town.strip()}%"),
        models.User.phone_number != sender
    ).all()

    next_three = matches[offset:offset + 3]

    if not next_three:
        return "No more matches available. SMS match#ageRange#town to start a new search."

    user.registration_stage = f"matching_{town}_{age_range}_{offset}"
    db.commit()

    remaining = len(matches) - (offset + 3)
    response = ""
    for match in next_three:
        response += f"{match.name} aged {match.age}, {match.phone_number}.\n"

    if remaining > 0:
        response += f"Send NEXT to 22141 to receive details of the remaining {remaining} matches."

    return response.strip()


def handle_profile_request(sender: str, message: str, db: Session) -> str:
    phone = message.strip()

    requested_user = db.query(models.User).filter(
        models.User.phone_number == phone
    ).first()

    if not requested_user:
        return f"No user found with phone number {phone}."

    requester = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if requester:
        notification = (
            f"Hi {requested_user.name}, a {requester.gender} called {requester.name} "
            f"is interested in you and requested your details. "
            f"They are aged {requester.age} based in {requester.town}. "
            f"Do you want to know more about them? Send YES to 22141."
        )
        save_message(db, "22141", requested_user.phone_number, notification, "outbound")

        requested_user.registration_stage = f"interested_{sender}"
        db.commit()

    return (
        f"{requested_user.name} aged {requested_user.age}, "
        f"{requested_user.county} County, {requested_user.town} town, "
        f"{requested_user.education or 'N/A'}, {requested_user.profession or 'N/A'}, "
        f"{requested_user.marital_status or 'N/A'}, {requested_user.religion or 'N/A'}, "
        f"{requested_user.ethnicity or 'N/A'}. "
        f"Send DESCRIBE {phone} to get more details about {requested_user.name}."
    )


def handle_describe(sender: str, message: str, db: Session) -> str:
    parts = message.strip().split(" ")
    if len(parts) != 2 or not is_phone_number(parts[1]):
        return "Invalid format. SMS DESCRIBE 07XXXXXXXX to 22141."

    phone = parts[1].strip()

    requested_user = db.query(models.User).filter(
        models.User.phone_number == phone
    ).first()

    if not requested_user:
        return f"No user found with phone number {phone}."

    if not requested_user.self_description:
        return f"{requested_user.name} has not provided a self description yet."

    return f"{requested_user.name} describes themselves as: {requested_user.self_description}"


def handle_yes(sender: str, db: Session) -> str:
    user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if not user or not user.registration_stage.startswith("interested_"):
        return "No pending interest to confirm."

    requester_phone = user.registration_stage.split("_")[1]

    requester = db.query(models.User).filter(
        models.User.phone_number == requester_phone
    ).first()

    if not requester:
        return "The person who requested your details is no longer available."

    user.registration_stage = "complete"
    db.commit()

    return (
        f"{requester.name} aged {requester.age}, "
        f"{requester.county} County, {requester.town} town, "
        f"{requester.education or 'N/A'}, {requester.profession or 'N/A'}, "
        f"{requester.marital_status or 'N/A'}, {requester.religion or 'N/A'}, "
        f"{requester.ethnicity or 'N/A'}. "
        f"Send DESCRIBE {requester_phone} to get more details about {requester.name}."
    )

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

@app.get("/messages")
def get_messages(db: Session = Depends(get_db)):
    messages = db.query(models.Message).all()
    return messages
