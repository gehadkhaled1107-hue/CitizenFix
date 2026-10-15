from datetime import datetime , timedelta


from constants import (
    STATUSES,
    TEAMS,
    DATETIME_FORMAT,
    PRIORITY_LABELS,
    PRIORITY_HOURS,
    CATEGORY_WEIGHTS,
    NEIGHBORHOOD_WEIGHTS
)
def calculate_priority(category: str, neighborhood: str = None) -> int:

    cat_score = CATEGORY_WEIGHTS.get(category, 1)
    neigh_score = NEIGHBORHOOD_WEIGHTS.get(neighborhood, 0)
    total_score = cat_score + neigh_score

    if total_score >= 4:
        return 1
    elif total_score == 3:
        return 2
    else:
        return 3 
    
from exceptions import ValidationError, MissingFieldError
from validators import (
    validate_ticket_id,
    validate_apartment_id,
    validate_name,
    validate_phone,
    validate_category,
    validate_priority,
    validate_neighborhood,
    validate_status,
    validate_team,
    validate_date
)

class Complaint():
    STATUS_TRANSITIONS = {
    "Pending":     {"Assigned", "Rejected"},
    "Assigned":    {"In Progress", "Rejected"},
    "In Progress": {"Resolved"},
    "Resolved":    set(),
    "Rejected":    set(),
    }
    
    REQUIRED_FIELDS = (
    "ticket_id", "apartment_id", "citizen_name", "phone",
    "category", "priority", "status", "created_at"
    )
    
    def __init__(self, ticket_id, apartment_id, citizen_name, phone,
                    category, priority = None, created_at=None, neighborhood=None):
        #user part
        self.ticket_id = validate_ticket_id(ticket_id)
        self.apartment_id = validate_apartment_id(apartment_id)
        self.citizen_name = validate_name(citizen_name)
        self.phone = validate_phone(phone)
        self.category = validate_category(category)
        self.priority = validate_priority(priority)
        self.neighborhood = validate_neighborhood(neighborhood)

        if priority is not None:
            self.priority = int(priority)
        else:
            self.priority = calculate_priority(self.category, self.neighborhood)
        
        #Admin part
        self.__status = STATUSES[0]
        self.__team = None
        
        if created_at is None:
            self.created_at = datetime.now().replace(second=0, microsecond=0)
        else:
            self.created_at = validate_date(created_at)
        
        self.deadline = self.created_at + timedelta(hours=PRIORITY_HOURS[self.priority])
        
    def get_status(self):
        return self.__status

    def set_status(self, new_status , force=False):
        if new_status not in STATUSES:
            return False
        elif not force and new_status not in self.STATUS_TRANSITIONS[self.__status]:
            return False
        self.__status = new_status
        return True

    def get_team(self):
        return self.__team

    def assign_to_team(self, team_name):
        if team_name not in TEAMS:
            return False
        elif not self.set_status("Assigned"):
            return False
        self.__team = team_name
        return True
    
    def comp_to_dict(self):
        return {
        "ticket_id": self.ticket_id,
        "apartment_id": self.apartment_id,
        "citizen_name": self.citizen_name,
        "phone": self.phone,
        "category": self.category,
        "priority": self.priority,
        "neighborhood": self.neighborhood,
        "status": self.__status,
        "team": self.__team,
        "created_at": self.created_at.strftime(DATETIME_FORMAT),
        "deadline": self.deadline.strftime(DATETIME_FORMAT),
    }
    
    def dict_to_comp(comp, data):
        if type(data) != dict:
            raise ValidationError("Complaint data must be a dictionary.", value=data)
        for field in comp.REQUIRED_FIELDS:
            if field not in data:
                raise MissingFieldError(f"Missing required field: {field}", value=field)
            
        dict_comp = comp(
            ticket_id=data["ticket_id"],
            apartment_id=data["apartment_id"],
            citizen_name=data["citizen_name"],
            phone=data["phone"],
            category=data["category"],
            priority=data["priority"],
            created_at=data["created_at"],
            neighborhood=data.get("neighborhood"),
        )
        
        dict_comp.set_status(validate_status(data["status"]), force=True)
        team_name = data.get("team")
        if team_name:
            dict_comp.__team = validate_team(team_name)
        return dict_comp


    def __str__(self):
        return (
            f"\n   CitizenFix | Complaint Receipt\n"
            f"Ticket ID    : {self.ticket_id}\n"
            f"Apartment    : {self.apartment_id}\n"
            f"Citizen      : {self.citizen_name}\n"
            f"Phone        : {self.phone}\n"
            f"Neighborhood : {self.neighborhood or '-'}\n"
            f"----------------------------------\n"
            f"Category     : {self.category}\n"
            f"Priority     : {PRIORITY_LABELS[self.priority]}\n"
            f"Status       : {self.__status}\n"
            f"Team         : {self.__team or 'Unassigned'}\n"
            f"----------------------------------\n"
            f"Created      : {self.created_at.strftime(DATETIME_FORMAT)}\n"
            f"SLA Deadline : {self.deadline.strftime(DATETIME_FORMAT)}\n"
        )