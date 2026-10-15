# FIXED FOR THE WHOLE PROGRAM
# safe import and easy to update

ROLES = (
    "Citizen",
    "OpsTeam",
    "Admin"
    )

ACTIONS = (
    "submit_complaint",
    "view_own_complaints",
    "view_all_complaints",
    "assign_complaint",
    "update_status",
    "view_reports",
)

CATEGORIES = (
    "Electricity",
    "Water",
    "Gas",
    "Sanitation",
    "Internet",
    "Security",
    "Road maintenance",
    "General",
)

STATUSES = (
    "Pending",
    "Assigned",
    "In Progress",
    "Resolved",
    "Rejected",
)

PRIORITY_LABELS = {
    1: "Urgent",
    2: "Medium",
    3: "Normal",
}

PRIORITY_HOURS = {
    1: 24,
    2: 72,
    3: 168,
}

TEAMS = (
    "Electricity Team",
    "Water & Gas Team",
    "Sanitation Team",
    "Internet & Security Team",
    "General Maintenance Team",
)

DATETIME_FORMAT = "%Y-%m-%d %H:%M"

TICKET_ID_PREFIX = "C-"
APARTMENT_ID_PREFIX = "ASIC"
ID_DIGITS = 4