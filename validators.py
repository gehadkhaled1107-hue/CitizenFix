import re
from datetime import datetime
from constants import (
    CATEGORIES,
    STATUSES,
    TEAMS,
    PRIORITY_LABELS,
    DATETIME_FORMAT,
    TICKET_ID_PREFIX,
    APARTMENT_ID_PREFIX,
    ID_DIGITS,
)
from exceptions import (
    InvalidPhoneError,
    InvalidTicketIdError,
    InvalidApartmentIdError,
    InvalidNameError,
    InvalidNeighborhoodError,
    InvalidCategoryError,
    InvalidPriorityError,
    InvalidStatusError,
    InvalidTeamError,
    InvalidDateError,
    InvalidDeadlineError,
)

ENGLISH_DIGITS = "0123456789"
ARABIC_TO_ENGLISH_DIGITS = {
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
}

PHONE_LENGTH = 11
VALID_PHONE_PREFIXES = ("010", "011", "012", "015")

TICKET_ID_PATTERN = re.compile(re.escape(TICKET_ID_PREFIX) + r"[0-9]{%d}" % ID_DIGITS)
APARTMENT_ID_PATTERN = re.compile(re.escape(APARTMENT_ID_PREFIX) + r"-[0-9]{%d}" % ID_DIGITS)

MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50

def validate_phone(phone):
    if type(phone) != str:
        raise InvalidPhoneError(value=phone)
    
    english_phone = ""
    for character in phone:
        if character == " " or character == "-":
            continue
        if character in ARABIC_TO_ENGLISH_DIGITS:
            character = ARABIC_TO_ENGLISH_DIGITS[character]
        english_phone += character
        
    if english_phone[:3] == "+20":
        english_phone = "0" + english_phone[3:]
    elif english_phone[:4] == "0020":
        english_phone = "0" + english_phone[4:]
        
    digits_count = 0
    for character in english_phone:
        if character not in ENGLISH_DIGITS:
            raise InvalidPhoneError(value=phone)
        digits_count += 1
        
    if digits_count != PHONE_LENGTH:
        raise InvalidPhoneError(value=phone)
    
    if english_phone[:3] not in VALID_PHONE_PREFIXES:
        raise InvalidPhoneError(value=phone)
    
    return english_phone

def validate_ticket_id(ticket_id):
    if type(ticket_id) != str:
        raise InvalidTicketIdError(value=ticket_id)
    cleaned_ticket_id = ticket_id.strip().upper()
    if not TICKET_ID_PATTERN.fullmatch(cleaned_ticket_id):
        raise InvalidTicketIdError(value=ticket_id)
    return cleaned_ticket_id

def validate_apartment_id(apartment_id):
    if type(apartment_id) != str:
        raise InvalidApartmentIdError(value=apartment_id)
    cleaned_apartment_id = apartment_id.strip().upper()
    if not APARTMENT_ID_PATTERN.fullmatch(cleaned_apartment_id):
        raise InvalidApartmentIdError(value=apartment_id)
    return cleaned_apartment_id

def contains_only_letters_and_spaces(text):
    for character in text:
        if not character.isalpha() and character != " ":
            return False
    return True

def validate_name(name):
    if type(name) != str:
        raise InvalidNameError(value=name)
    
    cleaned_name = name.strip()
    if len(cleaned_name) < MIN_NAME_LENGTH or len(cleaned_name) > MAX_NAME_LENGTH:
        raise InvalidNameError(value=name)
    
    if not contains_only_letters_and_spaces(cleaned_name):
        raise InvalidNameError(value=name)
    
    return cleaned_name

def validate_neighborhood(neighborhood):
    if neighborhood is None:
        return None
    
    if type(neighborhood) != str:
        raise InvalidNeighborhoodError(value=neighborhood)
    
    cleaned_neighborhood = neighborhood.strip()
    if cleaned_neighborhood == "":
        return None
    
    if len(cleaned_neighborhood) > MAX_NAME_LENGTH:
        raise InvalidNeighborhoodError(value=neighborhood)
    
    if not contains_only_letters_and_spaces(cleaned_neighborhood):
        raise InvalidNeighborhoodError(value=neighborhood)
    
    return cleaned_neighborhood

def find_official_option(value, official_options, error):
    if type(value) != str:
        raise error(value=value)
    
    wanted_option = value.strip().lower()
    
    for option in official_options:
        if option.lower() == wanted_option:
            return option
        
    raise error(value=value)

def validate_category(category):
    return find_official_option(category, CATEGORIES, InvalidCategoryError)

def validate_status(status):
    return find_official_option(status, STATUSES, InvalidStatusError)

def validate_team(team):
    return find_official_option(team, TEAMS, InvalidTeamError)

def validate_priority(priority):
    if type(priority) == str and priority.strip().isdecimal():
        priority = int(priority.strip())
    if type(priority) != int or priority not in PRIORITY_LABELS:
        raise InvalidPriorityError(value=priority)
    return priority

def validate_date(date):
    if type(date) == datetime:
        return date.replace(second=0, microsecond=0)
    if type(date) != str:
        raise InvalidDateError(value=date)
    cleaned_date = date.strip()
    
    try:
        object_datetime = datetime.strptime(cleaned_date, DATETIME_FORMAT)
    except ValueError:
        raise InvalidDateError(value=date)
    
    if object_datetime.strftime(DATETIME_FORMAT) != cleaned_date:
        raise InvalidDateError(value=date)
    return object_datetime

def validate_deadline(created_at, deadline):
    if deadline < created_at:
        raise InvalidDeadlineError(value=deadline)
    return deadline