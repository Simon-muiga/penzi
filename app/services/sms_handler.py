from sqlalchemy.orm import Session
from app import models
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_phone_number(text: str) -> bool:
    cleaned = text.strip().replace(" ", "")
    pattern = r'^(\+254|0)[17]\d{8}$'
    return bool(re.match(pattern, cleaned))


def clean_phone(phone: str) -> str:
    return phone.strip().replace(" ", "")


def save_message(
    db: Session,
    sender: str,
    receiver: str,
    message: str,
    direction: str
):
    try:
        new_message = models.Message(
            sender=sender,
            receiver=receiver,
            message=message,
            direction=direction
        )
        db.add(new_message)
        db.commit()
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        db.rollback()


def handle_message(sender: str, message: str, db: Session) -> str:
    # Edge case: empty message
    if not message or not message.strip():
        return "Invalid command. SMS PENZI to 22141 to get started."

    # Trim and normalize
    message = message.strip()

    try:
        if message.upper() == "PENZI":
            return (
                "Welcome to our dating service with potential dating partners! "
                "To register SMS start#name#age#gender#county#town to 22141. "
                "E.g., start#Nickson#22#Male#Nairobi#Kitengela"
            )

        if message.lower().startswith("start#"):
            return handle_registration(sender, message, db)

        if message.lower().startswith("details#"):
            return handle_details(sender, message, db)

        if message.upper().startswith("MYSELF"):
            return handle_self_description(sender, message, db)

        if message.lower().startswith("match#"):
            return handle_matching(sender, message, db)

        if message.upper().strip() == "NEXT":
            return handle_next(sender, db)

        if message.upper().startswith("DESCRIBE"):
            return handle_describe(sender, message, db)

        if message.upper().strip() == "YES":
            return handle_yes(sender, db)

        if is_phone_number(message):
            return handle_profile_request(sender, clean_phone(message), db)

        return "Invalid command. SMS PENZI to 22141 to get started."

    except Exception as e:
        logger.error(f"Error handling message from {sender}: {e}")
        return "Sorry, something went wrong. Please try again."


def handle_registration(sender: str, message: str, db: Session) -> str:
    parts = message.split("#")

    # Edge case: wrong number of parts
    if len(parts) != 6:
        return "Invalid format. SMS start#name#age#gender#county#town to 22141."

    _, name, age, gender, county, town = parts

    # Edge case: empty fields
    if not name.strip():
        return "Invalid format. Name cannot be empty."

    if not age.strip():
        return "Invalid format. Age cannot be empty."

    if not gender.strip():
        return "Invalid format. Gender cannot be empty."

    if not county.strip():
        return "Invalid format. County cannot be empty."

    if not town.strip():
        return "Invalid format. Town cannot be empty."

    # Edge case: age is not a number
    if not age.strip().isdigit():
        return "Invalid age. Please enter a valid number. E.g., start#Nickson#22#Male#Nairobi#Kitengela"

    age_int = int(age.strip())

    # Edge case: unrealistic age
    if age_int < 18:
        return "Sorry, you must be at least 18 years old to register."

    if age_int > 100:
        return "Invalid age. Please enter a valid age."

    # Edge case: invalid gender
    gender_clean = gender.strip().lower()
    if gender_clean not in ["male", "female", "m", "f"]:
        return "Invalid gender. Please use Male or Female."

    # Normalize gender
    gender_normalized = "Male" if gender_clean in ["male", "m"] else "Female"

    # Edge case: name too long
    if len(name.strip()) > 100:
        return "Name is too long. Please use a shorter name."

    # Edge case: duplicate registration
    existing_user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if existing_user:
        return f"You are already registered, {existing_user.name}. SMS match#ageRange#town to find a partner."

    new_user = models.User(
        phone_number=sender,
        name=name.strip(),
        age=age_int,
        gender=gender_normalized,
        county=county.strip(),
        town=town.strip(),
        registration_stage="basic"
    )
    db.add(new_user)
    db.commit()

    return (
        f"Your profile has been created successfully {name.strip()}. "
        "SMS details#levelOfEducation#profession#maritalStatus#religion#ethnicity to 22141. "
        "E.g. details#degree#engineer#single#christian#kikuyu"
    )


def handle_details(sender: str, message: str, db: Session) -> str:
    parts = message.split("#")

    if len(parts) != 6:
        return "Invalid format. SMS details#education#profession#maritalStatus#religion#ethnicity to 22141."

    _, education, profession, marital_status, religion, ethnicity = parts

    # Edge case: empty fields
    if not all([education.strip(), profession.strip(), marital_status.strip(), religion.strip(), ethnicity.strip()]):
        return "Invalid format. All fields are required. E.g. details#degree#engineer#single#christian#kikuyu"

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

    # Edge case: empty description
    if not description:
        return "Please provide a description after MYSELF. E.g., MYSELF tall, dark and funny"

    # Edge case: description too short
    if len(description) < 3:
        return "Description is too short. Please provide more details about yourself."

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

    # Edge case: empty town
    if not town.strip():
        return "Invalid format. Town cannot be empty. E.g., match#20-25#Nairobi"

    user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if not user:
        return "You are not registered. SMS PENZI to 22141 to get started."

    age_parts = age_range.split("-")

    # Edge case: invalid age range format
    if len(age_parts) != 2:
        return "Invalid age range. Use format like 20-25."

    if not age_parts[0].strip().isdigit() or not age_parts[1].strip().isdigit():
        return "Invalid age range. Use numbers only. E.g., match#20-25#Nairobi"

    min_age = int(age_parts[0].strip())
    max_age = int(age_parts[1].strip())

    # Edge case: min age greater than max age
    if min_age > max_age:
        return f"Invalid age range. Minimum age ({min_age}) cannot be greater than maximum age ({max_age})."

    # Edge case: unrealistic age range
    if min_age < 18:
        return "Minimum age must be at least 18."

    if max_age > 100:
        return "Maximum age cannot exceed 100."

    opposite_gender = "Female" if user.gender.lower() in ["male", "m"] else "Male"

    matches = db.query(models.User).filter(
        models.User.gender.ilike(f"%{opposite_gender}%"),
        models.User.age >= min_age,
        models.User.age <= max_age,
        models.User.town.ilike(f"%{town.strip()}%"),
        models.User.phone_number != sender
    ).all()

    if not matches:
        return f"Sorry, no matches found for age {age_range} in {town.strip()}. Try a different age range or town."

    user.registration_stage = f"matching_{town.strip()}_{age_range}_0"

    for match in matches:
        # Edge case: avoid duplicate match records
        existing = db.query(models.Match).filter(
            models.Match.requester_phone == sender,
            models.Match.matched_phone == match.phone_number
        ).first()
        if not existing:
            new_match = models.Match(
                requester_phone=sender,
                matched_phone=match.phone_number,
                status="pending"
            )
            db.add(new_match)

    db.commit()

    total = len(matches)
    first_three = matches[:3]
    opposite_label = "ladies" if opposite_gender == "Female" else "men"

    response = f"We have {total} {opposite_label} who match your choice! We will send you details of 3 of them shortly.\n"
    for match in first_three:
        response += f"{match.name} aged {match.age}, {match.phone_number}.\n"

    if total > 3:
        response += f"Send NEXT to 22141 to receive details of the remaining {total - 3} matches."

    return response.strip()


def handle_next(sender: str, db: Session) -> str:
    user = db.query(models.User).filter(
        models.User.phone_number == sender
    ).first()

    if not user:
        return "You are not registered. SMS PENZI to 22141 to get started."

    if not user.registration_stage.startswith("matching_"):
        return "You have no active search. SMS match#ageRange#town to 22141 to search."

    parts = user.registration_stage.split("_")

    # Edge case: malformed registration stage
    if len(parts) < 4:
        return "You have no active search. SMS match#ageRange#town to 22141 to search."

    town = parts[1]
    age_range = parts[2]

    try:
        offset = int(parts[3]) + 3
    except ValueError:
        return "You have no active search. SMS match#ageRange#town to 22141 to search."

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


def handle_profile_request(sender: str, phone: str, db: Session) -> str:
    # Edge case: requesting your own profile
    if phone == sender:
        return "You cannot request your own profile."

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
    parts = message.strip().split()

    # Edge case: DESCRIBE with no phone number
    if len(parts) < 2:
        return "Invalid format. SMS DESCRIBE 07XXXXXXXX to 22141."

    # Edge case: DESCRIBE with invalid phone number
    phone = clean_phone(parts[1])
    if not is_phone_number(phone):
        return f"Invalid phone number format. SMS DESCRIBE 07XXXXXXXX to 22141."

    # Edge case: describing yourself
    if phone == sender:
        return "You cannot request your own description."

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

    if not user:
        return "You are not registered. SMS PENZI to 22141 to get started."

    if not user.registration_stage.startswith("interested_"):
        return "No pending interest to confirm."

    parts = user.registration_stage.split("_")

    # Edge case: malformed registration stage
    if len(parts) < 2:
        return "No pending interest to confirm."

    requester_phone = parts[1]

    requester = db.query(models.User).filter(
        models.User.phone_number == requester_phone
    ).first()

    if not requester:
        return "The person who requested your details is no longer available."

    existing_match = db.query(models.Match).filter(
        models.Match.requester_phone == requester_phone,
        models.Match.matched_phone == sender
    ).first()

    if existing_match:
        existing_match.status = "accepted"

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