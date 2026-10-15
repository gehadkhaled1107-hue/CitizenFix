from datetime import datetime , timedelta
from constants import (
    STATUSES,
    TEAMS,
    DATETIME_FORMAT,
    PRIORITY_LABELS,
    PRIORITY_HOURS
)

class Complaint():
    STATUS_TRANSITIONS = {
    "Pending":     {"Assigned", "Rejected"},
    "Assigned":    {"In Progress", "Rejected"},
    "In Progress": {"Resolved"},
    "Resolved":    set(),
    "Rejected":    set(),
    }
    
    def __init__(self, ticket_id, apartment_id, citizen_name, phone,
                    category, priority, created_at=None, neighborhood=None):
        #user part
        self.ticket_id = ticket_id
        self.apartment_id = apartment_id
        self.citizen_name = citizen_name
        self.phone = phone
        self.category = category
        self.priority = priority
        self.neighborhood = neighborhood
        
        #Admin part
        self.__status = STATUSES[0]
        self.__team = None
        self.created_at = created_at if created_at else datetime.now().replace(second=0, microsecond=0)
        self.deadline = self.created_at + timedelta(hours=PRIORITY_HOURS[priority])
        
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
        try:
            dict_comp = comp(
                ticket_id=data["ticket_id"],
                apartment_id=data["apartment_id"],
                citizen_name=data["citizen_name"],
                phone=data["phone"],
                category=data["category"],
                priority=int(data["priority"]),
                created_at=datetime.strptime(data["created_at"], DATETIME_FORMAT),
                neighborhood=data.get("neighborhood"),
            )
            if not dict_comp.set_status(data["status"], force=True):
                return None
            dict_comp.__team = data.get("team") or None
            return dict_comp
        
        except Exception:
            return None

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
