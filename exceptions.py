class CitizenFixError(Exception):
    default_message = "Something went wrong"
    
    def __init__(self, message= None, value=None):
        self.message = message if message else self.default_message
        self.value = value
        super().__init__(self.message)

#input errors
class ValidationError(CitizenFixError):
    default_message = "Invalid input."

class MissingFieldError(ValidationError):
    default_message = "A required field is missing."

class InvalidPhoneError(ValidationError):
    default_message = ("Invalid phone number --> (e.g. 01012345678).")

class InvalidTicketIdError(ValidationError):
    default_message = "Invalid ticket ID --> (Ex: C-0001)"

class InvalidApartmentIdError(ValidationError):
    default_message = "Invalid apartment ID --> (Ex: ASIC-0001)"

class InvalidNameError(ValidationError):
    default_message = ("Invalid name --> Use 2 to 50 letters and spaces only")

class InvalidNeighborhoodError(ValidationError):
    default_message = "Invalid neighborhood --> Use letters and spaces only or leave it empty."

class InvalidCategoryError(ValidationError):
    default_message = """Invalid category --> It must be one of 
    ("Electricity","Water","Gas","Sanitation","Internet","Security","Road maintenance","General")"""

class InvalidPriorityError(ValidationError):
    default_message = "Invalid priority --> It must be 1 (Urgent), 2 (Medium) or 3 (Normal)."

class InvalidStatusError(ValidationError):
    default_message = 'Invalid status --> It must be one of ("Pending","Assigned","In Progress","Resolved","Rejected")'

class InvalidTeamError(ValidationError):
    default_message = """Invalid team --> It must be one of 
    ("Electricity Team","Water & Gas Team","Sanitation Team","Internet & Security Team","General Maintenance Team")"""

class InvalidDateError(ValidationError):
    default_message = ("Invalid date --> Use the format YYYY-MM-DD HH:MM ")

class InvalidDeadlineError(ValidationError):
    default_message = "Invalid deadline --> It cannot be earlier than the creation time"

class InvalidRoleError(ValidationError):
    default_message = "Invalid role --> It must be Citizen, OpsTeam or Admin"

#complaint workflow
class ComplaintError(CitizenFixError):
    default_message = "Complaint error"

class InvalidStatusTransitionError(ComplaintError):
    default_message = "This status change is not allowed by the workflow"

class ComplaintNotFoundError(ComplaintError):
    default_message = "No complaint found with this ticket ID"

class DuplicateTicketError(ComplaintError):
    default_message = "A complaint with this ticket ID already exists"

class NothingToUndoError(ComplaintError):
    default_message = "There is no action to undo"

class EmptyQueueError(ComplaintError):
    default_message = "There are no complaints in the queue"

#permissions
class PermissionDeniedError(CitizenFixError):
    default_message = "Your role is not allowed to do this action"

#auth --> Extra for bonus if we make it
class AuthError(CitizenFixError):
    default_message = "Authentication error"

class LoginError(AuthError):
    default_message = "Invalid username or password"

class AccountLockedError(AuthError):
    default_message = "Too many failed attempts -- Try again later"

#data
class DataError(CitizenFixError):
    default_message = "Data error"

class DataLoadError(DataError):
    default_message = "Could not load the data file"

class DataSaveError(DataError):
    default_message = "Could not save the data file"