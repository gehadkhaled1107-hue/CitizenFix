import csv
import os
from collections import Counter
from datetime import datetime

from constants import (
    ROLES, CATEGORIES, STATUSES, TEAMS, PRIORITY_LABELS,
    NEIGHBORHOOD_WEIGHTS, DATETIME_FORMAT, TICKET_ID_PREFIX, ID_DIGITS,
)
from exceptions import (
    CitizenFixError, ComplaintNotFoundError, DuplicateTicketError,
    InvalidStatusTransitionError, InvalidDateError, DataSaveError, DataLoadError
)
from complaint import Complaint, calculate_priority
from users import create_user_by_role
from validators import validate_phone, validate_ticket_id
from json_functions import load_data, save_data
from Algorithm import (
    ComplaintQueue, ComplaintPriorityQueue, ComplaintSorter,
    TeamSelection, DuplicateDetector, UndoStack,
    build_complaint_index, hash_lookup, sequential_search,
    binary_search_by_id,
)
from Searchtypes import (
    PhoneHashSearch, TeamHashSearch, DateBinarySearch,
    CategorySequentialSearch, TicketHashSearch,
)

# Handle --> find the path --> json/csv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "Tickets.json")
CSV_FILE = os.path.join(BASE_DIR, "complaints_1000.csv")

FINISHED_STATUSES = ("Resolved", "Rejected")
ACTIVE_STATUSES = ("Pending", "Assigned", "In Progress")

STAFF_CODE = "staff123"

#  Helper function to apply DRY CODE  #
# same block appear to many times at first  #

# for handling the input format once for all program
def ask(inp):
    return input(inp).strip()

# display the menu by enumerate
# options[int(answer) - 1] --> real index start from 0 but menu from 1
def choose(title, options, break_point="cancel"):
    print("\n" + title)
    for number, option in enumerate(options, start=1):
        print(f"{number}. {option}")

    while True:
        answer = ask(f"Choose a number (0 = {break_point}): ")
        if answer == "0":
            return None
        if answer.isdecimal() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print("Invalid choice, try again.")

# show 15 complaints by default 
# if there is more print note for the user
def show_list(complaints, limit=15):
    if not complaints:
        print("\nNo complaints found.")
        return

    print("\nID || Status || Priority || Category || Team || Deadline")
    print("--" * 40)

    for c in complaints[:limit]:
        print(
            c.ticket_id,
            c.get_status(),
            PRIORITY_LABELS[c.priority],
            c.category,
            c.get_team() or "-",
            c.deadline.strftime(DATETIME_FORMAT),
            sep=" || ",
        )

    if len(complaints) > limit:
        print(f"... showing {limit} of {len(complaints)}")

# take a list and count repetition by default
# show it in order or from top or all of them
def show_counts(title, values, order=None, top=None):
    counts = Counter(values)
    # _ --> to ignore the count as we don't need it
    keys = order or [key for key, _ in counts.most_common(top)]
    print("\n" + title)
    print("--" * 40)
    for key in keys:
        print(key, counts[key], sep=" || ")

#convert the json file data to complaints and validate it
# return the complaints and the num of skipped raws (invalid)
def build_complaints(rows):
    complaints = []
    for row in rows:
        try:
            complaints.append(Complaint.dict_to_comp(row))
        except CitizenFixError:
            pass  # bad row -> skip it
    return complaints, len(rows) - len(complaints)


# The Program runner class #
class CitizenFixApp:
    def __init__(self):
        self.user = None
        self.undo_stack = UndoStack()
        self.complaints = []
        self.index = {}
        self.teams = TeamSelection(TEAMS)
        self.load()
        self.rebuild()

    # data handling
    # loading the data from json file 
    #convert it to complaints
    def load(self):
        try:
            rows = load_data(DATA_FILE)
        except DataLoadError as error:
            print(f"Warning: {error.message}")
            rows = []

        self.complaints, skipped = build_complaints(rows)

        # first run --> json is empty -- > so import the CSV
        if not self.complaints and os.path.exists(CSV_FILE):
            with open(CSV_FILE, encoding="utf-8", newline="") as file:
                self.complaints, skipped = build_complaints(list(csv.DictReader(file)))
            self.save()
            print("Imported complaints from CSV")
        print(f"Loaded {len(self.complaints)} complaints ({skipped} invalid rows skipped)")

    #convert it to dict to save in json
    def save(self):
        try:
            save_data([c.comp_to_dict() for c in self.complaints], DATA_FILE)
        except DataSaveError as error:
            print(f"Error: {error.message}")

    # Refresh the ticket index and the active workload of every team
    # give the complaint index then find the team and +1 the complaint count
    def rebuild(self):
        self.index = build_complaint_index(self.complaints)
        self.teams = TeamSelection(TEAMS)

        for c in self.complaints:
            if c.get_team() in self.teams.team_workload and c.get_status() in ACTIVE_STATUSES:
                self.teams.team_workload[c.get_team()] += 1

    # calculate next ticket id 
    def next_ticket_id(self):
        last = max((int(t[len(TICKET_ID_PREFIX):]) for t in self.index), default=0)
        return TICKET_ID_PREFIX + str(last + 1).zfill(ID_DIGITS)

    # add a complaints if not exists and add it to index dict
    def add_complaint(self, complaint):
        if hash_lookup(self.index, complaint.ticket_id):
            raise DuplicateTicketError(value=complaint.ticket_id)

        self.complaints.append(complaint)
        self.index[complaint.ticket_id] = complaint
        self.save()

    # check if the complaint ticket_id valid and existed
    def lookup(self, ticket_id):
        ticket_id = validate_ticket_id(ticket_id)
        complaint = hash_lookup(self.index, ticket_id)
        if complaint is None:
            raise ComplaintNotFoundError(value=ticket_id)
        return complaint

    # ask the user for ticket_id and apply lookup()
    def ask_ticket(self):
        return self.lookup(ask("Ticket ID (e.g. C-0001): "))

    # display the complaint 
    # a citizen sees only their own
    def open_receipt(self, action):
        ticket_id = ask("\nTicket ID to see full details (Enter to skip): ")
        if ticket_id:
            complaint = self.lookup(ticket_id)
            self.user.require_access(action, complaint)
            print(complaint)

    # menu
    def menu_items(self):
        # (permission needed, label, function)
        menu = [
            ("submit_complaint", "Submit a complaint", self.submit_complaint),
            ("view_own_complaints", "My complaints", self.my_complaints),
            ("view_all_complaints", "View all complaints", self.view_all),
            ("view_all_complaints", "Search complaints", self.search),
            ("assign_complaint", "Assign most urgent complaint", self.assign_next),
            ("assign_complaint", "Assign by ticket ID", self.assign_by_ticket),
            ("update_status", "Update complaint status", self.update_status),
            ("update_status", f"Undo last change ({self.undo_stack.size()})", self.undo),
            ("view_reports", "Reports", self.reports),
        ]
        # display the allowed actions
        def allowed(action):
            if action == "view_own_complaints":
                return self.user.role == "Citizen"
            return self.user.has_permission(action)
        return [(label, function) for action, label, function in menu if allowed(action)]

    # run user menu
    def menu(self):
        while True:
            items = self.menu_items()

            print(f"\n{self.user.home_page_title()} || {self.user}")
            print("--" * 40)
            for number, (label, _) in enumerate(items, start=1):
                print(f"{number}. {label}")
            print("S. Switch user")
            print("0. Save and exit")

            answer = ask("> ").lower()

            if answer == "0":
                return False
            if answer == "s":
                return True

            if answer.isdecimal() and 1 <= int(answer) <= len(items):
                try:
                    items[int(answer) - 1][1]() # implement the function
                except CitizenFixError as error:
                    print(f"Error: {error.message}")
            else:
                print("Invalid choice.")

    # citizen
    def submit_complaint(self):
        print("\nSubmit a complaint")
        print("--" * 40)

        apartment = getattr(self.user, "apartment_id", None)
        if apartment:
            print("Apartment:", apartment)
        else:
            apartment = ask("Apartment ID (e.g. ASIC-0001): ")

        name = ask("Citizen name: ")
        phone = ask("Phone: ")

        category = choose("Category:", CATEGORIES)
        if category is None:
            return

        neighborhood = choose("Neighborhood:", list(NEIGHBORHOOD_WEIGHTS), break_point="skip")
        priority = calculate_priority(category, neighborhood)

        complaint = Complaint(
            self.next_ticket_id(), apartment, name, phone, category,
            priority, neighborhood=neighborhood,
        )

        duplicate = DuplicateDetector().find_duplicates(complaint, self.complaints)
        if duplicate:
            print(f"\nA similar open complaint exists: {duplicate.ticket_id}")
            if ask("Submit anyway? (y/n): ").lower() != "y":
                return

        self.add_complaint(complaint)
        print("\nComplaint submitted successfully.")
        print(complaint)

    def my_complaints(self):
        mine = [c for c in self.complaints if self.user.permission("view_own_complaints", c)]
        show_list(mine, 20)
        self.open_receipt("view_own_complaints")

    # staff

    def view_all(self):
        status = choose("Filter by status:", STATUSES, "all")
        sort_by = choose("Sort by:", ("priority", "deadline", "created_at"), "priority")

        data = [c for c in self.complaints if status is None or c.get_status() == status]

        sorter = ComplaintSorter()
        result = sorter.merge_sort(data, by=sort_by or "priority")

        show_list(result)
        print(f"\nMerge sort || {sorter.comparisons} comparisons || {sorter.recursive_calls} recursive calls")
        self.open_receipt("view_all_complaints")

    def search(self):
        complaints = self.complaints
        options = (
            "Ticket ID (hash lookup)",
            "Ticket ID (binary search)",
            "Phone number (hash lookup)",
            "Category (sequential search)",
            "Citizen name (sequential search)",
            "Created date (binary search)",
            "Team (hash lookup)",
        )

        kind = choose("Search by:", options)
        if kind is None:
            return

        results = []

        if kind == options[0]:
            found = TicketHashSearch(complaints).search(validate_ticket_id(ask("Ticket ID: ")))
            results = [found] if found else []

        elif kind == options[1]:
            ticket_id = validate_ticket_id(ask("Ticket ID: "))
            by_id = sorted(complaints, key=lambda c: c.ticket_id)  # binary search needs sorted data
            found = binary_search_by_id(by_id, ticket_id)
            results = [found] if found else []

        elif kind == options[2]:
            results = PhoneHashSearch(complaints).search(validate_phone(ask("Phone: ")))

        elif kind == options[3]:
            category = choose("Category:", CATEGORIES)
            if category:
                results = CategorySequentialSearch(complaints).search(category)

        elif kind == options[4]:
            results = sequential_search(complaints, "citizen_name", ask("Name or part of name: "))

        elif kind == options[5]:
            date = ask("Date (YYYY-MM-DD): ")
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise InvalidDateError("Invalid date --> Use the format YYYY-MM-DD", value=date)
            results = DateBinarySearch(complaints).search(date)

        elif kind == options[6]:
            team = choose("Team:", TEAMS)
            if team:
                found = TeamHashSearch(complaints).search(TEAMS.index(team) + 1)
                results = found["complaints"]

        show_list(results)
        self.open_receipt("view_all_complaints")

    def assign(self, complaint):
        self.user.require_access("assign_complaint", complaint)

        # save it to record if assign success
        prev_status = complaint.get_status()
        prev_team = complaint.get_team()

        team = self.teams.assign_team(complaint)
        if team is None:
            print(f"Cannot assign {complaint.ticket_id} || Current status: {prev_status}.")
            return

        self.undo_stack.record_action(complaint, prev_status, prev_team, team, complaint.get_status())
        self.save()
        print(f"Assigned {complaint.ticket_id} to {team}.")

    # combine the pending complaints
    def assign_next(self):
        pending = [c for c in self.complaints if c.get_status() == "Pending"]
        if not pending:
            print("No pending complaints.")
            return

        # store it in queue
        queue = ComplaintPriorityQueue()
        for c in pending:
            queue.push(c)

        print(f"\n{queue.size()} pending complaints (most urgent first)")
        show_list(queue.to_list(), 5)
        print(f"Priority queue || {queue.comparisons} comparisons")

        if ask("Assign the most urgent one? (y/n): ").lower() == "y":
            self.assign(queue.pop())

    def assign_by_ticket(self):
        self.assign(self.ask_ticket())

    # check allowed status and permission before update
    def update_status(self):
        complaint = self.ask_ticket()
        self.user.require_access("update_status", complaint)

        current = complaint.get_status()
        team = complaint.get_team()
        allowed = Complaint.STATUS_TRANSITIONS[current]

        # "Assigned" is handled by the Assign options so the team gets chosen too
        options = [s for s in STATUSES if s in allowed and s != "Assigned"]

        if "Assigned" in allowed:
            print("Use the Assign option to set status to Assigned")
        if not options:
            print(f"{complaint.ticket_id} cannot change status from {current}")
            return
        new_status = choose(f"{complaint.ticket_id} is {current} --> Move to:", options)
        if new_status is None:
            return
        
        # change the status --> False means the workflow does not allow it
        if not complaint.set_status(new_status):
            raise InvalidStatusTransitionError(value=new_status)
        
        if new_status in FINISHED_STATUSES and team:
            self.teams.release_team(team)

        self.undo_stack.record_action(complaint, current, team, team, new_status)
        self.save()
        print(f"{complaint.ticket_id} || {current} -> {new_status}")

    def undo(self):
        action = self.undo_stack.undo()
        self.rebuild()
        self.save()
        print(f"Undone: {action.complaint.ticket_id} is back to {action.prev_status}.")

    # admin
    # numbers only --> counts, team workload, overdue complaints
    def reports(self):
        complaints = self.complaints
        print(f"\nReports || {len(complaints)} complaints")
        show_counts("By status", [c.get_status() for c in complaints], order=STATUSES)
        show_counts("By category", [c.category for c in complaints])
        show_counts(
            "By priority",
            [PRIORITY_LABELS[c.priority] for c in complaints],
            order=list(PRIORITY_LABELS.values()),
        )
        show_counts("Top 5 neighborhoods", [c.neighborhood or "Unknown" for c in complaints], top=5)

        print("\nActive workload per team")
        print("--" * 40)
        for team, workload in self.teams.team_workload.items():
            print(team, workload, sep=" || ")

        # overdue --> still active and the deadline already passed
        now = datetime.now()
        overdue = [c for c in complaints if c.get_status() in ACTIVE_STATUSES and c.deadline < now]
        overdue = ComplaintSorter().merge_sort(overdue, by="deadline")

        queue = ComplaintQueue()
        for c in overdue:
            queue.enqueue(c)

        print(f"\nOverdue active complaints || {queue.size()}")
        if not queue.is_empty():
            print(f"Most overdue || {queue.peek().ticket_id}")

    # login 
    # ask who is using the program --> create the matching user object
    def select_user(self):
        username = ask("Username (0 = exit): ") or "Citizen"

        if username == "0":
            return False
        if username == STAFF_CODE:
            return self.staff_login()

        apartment_id = ask("Apartment ID (e.g. ASIC-0001): ")
        self.user = create_user_by_role("Citizen", username, apartment_id=apartment_id)
        return True

    def staff_login(self):
        role = choose("Select staff role:", ROLES[1:])
        if role is None:
            return None

        username = ask("Your name: ") or role
        team_name = None

        if role == "OpsTeam":
            team_name = choose("Select team:", TEAMS)
            if team_name is None:
                return None

        self.user = create_user_by_role(role, username, team_name=team_name)
        return True

    def run(self):
        print("\n||| ||  CitizenFix  || ||| ")
        
        while True:
            try:
                result = self.select_user()
            except CitizenFixError as error:
                print(f"Error: {error.message}")
                continue

            if result is False:
                break
            if result is None:
                continue

            if not self.menu():
                break


def main():
    app = CitizenFixApp()

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
    finally:
        app.save()

    print("SAVED -- SEE YOU AGAIN !")


if __name__ == "__main__":
    main()