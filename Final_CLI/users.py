from CitizenFix.Final_CLI.constants import ROLES, ACTIONS
from CitizenFix.Final_CLI.exceptions import InvalidRoleError, PermissionDeniedError
from CitizenFix.Final_CLI.validators import validate_team, validate_apartment_id, find_official_option
from CitizenFix.Final_CLI.complaint import Complaint

CITIZEN_ACTIONS = ("submit_complaint", "view_own_complaints")
STAFF_ACTIONS = ("view_all_complaints", "assign_complaint", "update_status")
ADMIN_EXTRA_ACTIONS = ("submit_complaint", "view_own_complaints", "view_reports")


class User():
    def __init__(self, username, role):
        self.username = username
        self.role = role

    def has_permission(self, action):
        return False

    def complaint_rule(self, action, complaint):
        return True

    def permission(self, action, complaint):
        if not self.has_permission(action):
            return False
        if not isinstance(complaint, Complaint):
            return False
        if not self.complaint_rule(action, complaint):
            return False
        return True

    def allowed_actions(self):
        allowed = []
        for action in ACTIONS:
            if self.has_permission(action):
                allowed.append(action)
        return allowed

    def require_permission(self, action):
        if not self.has_permission(action):
            raise PermissionDeniedError(
                f"{self.role} '{self.username}' is not allowed to: {action}", value=action
            )

    def require_access(self, action, complaint):
        if not self.permission(action, complaint):
            raise PermissionDeniedError(
                f"{self.role} '{self.username}' is not allowed to {action} on this complaint",
                value=action,
            )

    def home_page_title(self):
        return "Home"

    def __str__(self):
        return f"{self.username} --> {self.role}"


class StaffUser(User):
    def has_permission(self, action):
        if action in STAFF_ACTIONS:
            return True
        return False


class Citizen(User):
    def __init__(self, username, apartment_id=None):
        super().__init__(username, "Citizen")
        self.apartment_id = None
        if apartment_id is not None:
            self.apartment_id = validate_apartment_id(apartment_id)

    def has_permission(self, action):
        if action in CITIZEN_ACTIONS:
            return True
        return False

    def complaint_rule(self, action, complaint):
        if self.apartment_id is None:
            return False
        if action != "view_own_complaints":
            return False
        if complaint.apartment_id != self.apartment_id:
            return False
        return True

    def home_page_title(self):
        return "My complaints"


class OpsTeam(StaffUser):
    def __init__(self, username, team_name):
        super().__init__(username, "OpsTeam")
        self.team_name = validate_team(team_name)

    def complaint_rule(self, action, complaint):
        if action == "view_all_complaints":
            return True

        if action == "assign_complaint":
            if complaint.get_team() is None:
                return True
            if complaint.get_team() == self.team_name:
                return True
            return False

        if complaint.get_team() == self.team_name:
            return True
        return False

    def home_page_title(self):
        return f"{self.team_name} dashboard"


class Admin(StaffUser):
    def __init__(self, username):
        super().__init__(username, "Admin")

    def has_permission(self, action):
        if super().has_permission(action):
            return True
        if action in ADMIN_EXTRA_ACTIONS:
            return True
        return False

    def home_page_title(self):
        return "Admin dashboard"


def create_user_by_role(role, username, team_name=None, apartment_id=None):
    official_role = find_official_option(role, ROLES, InvalidRoleError)

    if official_role == "Citizen":
        return Citizen(username, apartment_id)
    if official_role == "OpsTeam":
        return OpsTeam(username, team_name)
    return Admin(username)