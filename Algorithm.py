from datetime import timedelta


from exceptions import EmptyQueueError, NothingToUndoError
from constants import CATEGORY_PRIMARY_TEAMS
import complaint


class ComplaintQueue:
    def __init__(self):
        self._item = []

    def enqueue(self, complaints_obj):
        self._item.append(complaints_obj)

    def is_empty(self):
        return len(self._item) == 0

    def dequeue(self):
        if self.is_empty():
            raise EmptyQueueError("Queue is empty")
        return self._item.pop(0)

    def size(self):
        return len(self._item)

    def peek(self):
        if self.is_empty():
            raise EmptyQueueError("Queue is empty")
        return self._item[0]

    def to_list(self):
        return list(self._item)


# PRIORITY QUEUE
class ComplaintPriorityQueue:
    def __init__(self):
        self._items = []
        self.comparisons = 0

    def _is_higher_urgency(self, c1, c2):
        self.comparisons += 1
        if c1.priority != c2.priority:
            return c1.priority < c2.priority
        return c1.deadline < c2.deadline

    def push(self, complaints_obj):
        if not self._items:
            self._items.append(complaint)
            return

        inserted = False
        for i in range(len(self._items)):
            if self._is_higher_urgency(complaints_obj, self._items[i]):
                self._items.insert(i, complaint)
                inserted = True
                break

        if not inserted:
            self._items.append(complaint)

    def pop(self):
        if self.is_empty():
            raise EmptyQueueError("Priority queue is empty.")
        return self._items.pop(0)

    def peek(self):
        if self.is_empty():
            raise EmptyQueueError("Priority queue is empty.")
        return self._items[0]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def to_list(self):
        return list(self._items)


# Merge sort by deadline, priority, created_at
class ComplaintSorter:
    def __init__(self):
        self.comparisons = 0
        self.recursive_calls = 0

    def sort_by(self, c1, c2, by="priority", reverse=False):
        self.comparisons += 1

        if by == "priority":
            if c1.priority != c2.priority:
                result = c1.priority < c2.priority
            else:
                result = c1.deadline < c2.deadline

        elif by == "created_at":
            if not reverse:
                result = c1.created_at > c2.created_at  # Newest first
            else:
                result = c1.created_at < c2.created_at  # Oldest first

        elif by == "deadline":
            if not reverse:
                result = c1.deadline < c2.deadline      # Earliest deadline first
            else:
                result = c1.deadline > c2.deadline
        else:
            result = True

        return result

    def merge_sort(self, complaints, by="priority", reverse=False):
        self.comparisons = 0
        self.recursive_calls = 0
        return self.divide_and_conquer(list(complaints), by, reverse)

    def divide_and_conquer(self, arr, by="priority", reverse=False):
        self.recursive_calls += 1
        if len(arr) <= 1:
            return arr

        mid = len(arr) // 2
        left = arr[:mid]
        right = arr[mid:]

        sorted_left = self.divide_and_conquer(left, by, reverse)
        sorted_right = self.divide_and_conquer(right, by, reverse)

        return self._merge(sorted_left, sorted_right, by, reverse)


    def _merge(self, left, right, by, reverse):
        merged = []
        i = j = 0

        while i < len(left) and j < len(right):
            if self.sort_by(left[i], right[j], by, reverse):
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged


def sequential_search(complaints, field, target):

    if not target:
        return []

    target_str = str(target).strip().lower()
    matches = []

    for comp in complaints:
        val = getattr(comp, field, None)
        if val is not None and target_str in str(val).strip().lower():
            matches.append(comp)

    return matches


def binary_search_by_id(sorted_complaints, target_id):

    if not sorted_complaints or not target_id:
        return None

    target_id_str = str(target_id).strip()
    low = 0
    high = len(sorted_complaints) - 1

    while low <= high:
        mid = (low + high) // 2
        mid_id = sorted_complaints[mid].ticket_id

        if mid_id == target_id_str:
            return sorted_complaints[mid]
        elif mid_id < target_id_str:
            low = mid + 1
        else:
            high = mid - 1

    return None

# Best team selection
class TeamSelection:
    def __init__(self, teams):
        self.teams = teams
        self.team_workload = {team: 0 for team in self.teams}

    def get_best_team(self, complaint_obj):
        eligible_teams = CATEGORY_PRIMARY_TEAMS.get(
            complaint_obj.category, ["General Maintenance Team"]
        )
        return min(eligible_teams, key=lambda t: self.team_workload[t])

    def assign_team(self, complaint_obj):
        selected_team = self.get_best_team(complaint_obj)
        assigned = complaint_obj.assign_to_team(selected_team)

        if assigned:
            self.team_workload[selected_team] += 1
            return selected_team
        return None

    def release_team(self, team_name):
        if team_name in self.team_workload and self.team_workload[team_name] > 0:
            self.team_workload[team_name] -= 1
        return team_name


# Detect duplicate complaint
class DuplicateDetector:
    def __init__(self, time_window_hours=6):
        self.time_window_hours = time_window_hours

    def find_duplicates(self, new_complaint, existing_complaints):
        for comp in existing_complaints:
            if (comp.apartment_id == new_complaint.apartment_id and
                    comp.category == new_complaint.category and
                    comp.get_status() not in ["Resolved", "Rejected"]):

                time_diff = abs(new_complaint.created_at - comp.created_at)

                if time_diff <= timedelta(hours=self.time_window_hours):
                    return comp
        return None


def build_complaint_index(complaints):

    return {comp.ticket_id: comp for comp in complaints}

def hash_lookup(complaint_index, complaint_id):

    if not complaint_index or not complaint_id:
        return None
    return complaint_index.get(str(complaint_id).strip())


# Undo Stack
class UndoAction:
    def __init__(self, complaint_obj, prev_status, prev_team, new_team, new_status):
        self.complaint = complaint_obj
        self.prev_status = prev_status
        self.prev_team = prev_team
        self.new_team = new_team
        self.new_status = new_status

    def revert(self):
        self.complaint.set_status(self.prev_status, force=True)
        self.complaint._Complaint__team = self.prev_team


class UndoStack:
    def __init__(self):
        self._history = []

    def is_empty(self):
        return len(self._history) == 0

    def record_action(self, complaint_obj, prev_status, prev_team, new_team, new_status):
        action = UndoAction(complaint_obj, prev_status, prev_team, new_team, new_status)
        self._history.append(action)

    def undo(self):
        if self.is_empty():
            raise NothingToUndoError("No actions available to undo.")
        last_action = self._history.pop()
        last_action.revert()
        return last_action

    def peek(self):
        if self.is_empty():
            raise NothingToUndoError("Undo stack is empty.")
        return self._history[-1]

    def size(self):
        return len(self._history)

    def clear(self):
        self._history.clear()