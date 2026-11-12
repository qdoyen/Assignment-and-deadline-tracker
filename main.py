from drafter import *
from datetime import date

COURSES = ["CISC106", "MEEG102", "MEEG112", "MEEG241", "PHYS227",
           "MATH232", "Other"]
ALL_COURSES = "All"
DEFAULT_USERNAME = "Student"


@dataclass
class Assignment:
    """One piece of work that has a course, a due date, and a time estimate."""
    title: str
    course: str
    due_date: str  
    hours_estimated: float
    high_priority: bool
    done: bool


@dataclass
class State:
    """Everything the website remembers between pages."""
    assignments: list[Assignment]
    username: str
    current_filter: str
    total_completed: int


def get_today() -> str:
    """Return today's date as text in YYYY-MM-DD form."""
    return date.today().isoformat()


def is_valid_date(text: str) -> bool:
    """Check that text looks like a real YYYY-MM-DD date, e.g. 2026-11-20."""
    if len(text) != 10:
        return False
    if text[4] != "-" or text[7] != "-":
        return False
    year, month, day = text[0:4], text[5:7], text[8:10]
    if not (year.isdigit() and month.isdigit() and day.isdigit()):
        return False
    return 1 <= int(month) <= 12 and 1 <= int(day) <= 31


def is_valid_hours(text: str) -> bool:
    """Check that text is a number greater than zero, such as 3 or 2.5."""
    cleaned = text.strip()
    if cleaned.count(".") > 1:
        return False
    digits = cleaned.replace(".", "")
    if digits == "" or not digits.isdigit():
        return False
    return float(cleaned) > 0


def format_hours(hours: float) -> str:
    """Show whole numbers without a decimal point, e.g. 3.0 becomes 3."""
    if hours == int(hours):
        return str(int(hours))
    return str(round(hours, 1))


def find_assignment_index(assignments: list[Assignment], title: str) -> int:
    """Return the position of the assignment with this title, or -1."""
    for position, assignment in enumerate(assignments):
        if assignment.title == title:
            return position
    return -1


def check_new_assignment(assignments: list[Assignment], title: str,
                         due_date: str, hours: str) -> str:
    """Return a message describing what is wrong with the form, or ''."""
    if title.strip() == "":
        return "Please enter a title."
    if find_assignment_index(assignments, title.strip()) != -1:
        return "You already have an assignment with that title."
    if not is_valid_date(due_date.strip()):
        return "The due date must look like 2026-11-20."
    if not is_valid_hours(hours):
        return "Hours must be a number greater than 0."
    return ""


def is_overdue(assignment: Assignment, today: str) -> bool:
    """An assignment is overdue if it is not done and its date has passed."""
    return not assignment.done and assignment.due_date < today


def count_overdue(assignments: list[Assignment], today: str) -> int:
    """Count how many assignments are overdue."""
    total = 0
    for assignment in assignments:
        if is_overdue(assignment, today):
            total += 1
    return total


def count_done(assignments: list[Assignment]) -> int:
    """Count how many assignments are finished."""
    total = 0
    for assignment in assignments:
        if assignment.done:
            total += 1
    return total


def total_hours_remaining(assignments: list[Assignment]) -> float:
    """Add up the estimated hours of every assignment that is not done."""
    total = 0.0
    for assignment in assignments:
        if not assignment.done:
            total += assignment.hours_estimated
    return total


def matches_filter(assignment: Assignment, current_filter: str) -> bool:
    """Decide whether an assignment should be shown for the chosen course."""
    if current_filter == ALL_COURSES:
        return True
    return assignment.course == current_filter


def get_due_date(assignment: Assignment) -> str:
    """Return the due date of an assignment (used for sorting)."""
    return assignment.due_date


def sort_by_due_date(assignments: list[Assignment]) -> list[Assignment]:
    """Return a new list ordered from the earliest due date to the latest.
    """
    return sorted(assignments, key=get_due_date)


def get_status(assignment: Assignment, today: str) -> str:
    """Return the status text shown in the table for one assignment."""
    if assignment.done:
        return "Done"
    if is_overdue(assignment, today):
        return "OVERDUE"
    return "To do"


def make_table_row(assignment: Assignment, today: str) -> list:
    """Build one table row: details plus a Mark done button if needed."""
    title = assignment.title
    if assignment.high_priority:
        title = title + " (high priority)"
    if assignment.done:
        action = ""
    else:
        action = Button("Mark done", mark_done,
                        [Argument("title", assignment.title)])
    return [title, assignment.course, assignment.due_date,
            format_hours(assignment.hours_estimated),
            get_status(assignment, today), action]


@route
def index(state: State) -> Page:
    """Dashboard: hours left, overdue warning, and links to every page."""
    overdue = count_overdue(state.assignments, get_today())
    hours_left = total_hours_remaining(state.assignments)
    if overdue > 0:
        warning = f"Warning: {overdue} assignment(s) are overdue!"
    else:
        warning = "Nothing is overdue."
    return Page(state, [
        Header(f"Assignment tracker for {state.username}", 1),
        f"Hours of work left: {format_hours(hours_left)}",
        warning,
        f"Assignments finished: {state.total_completed}",
        Button("Add assignment", add_page),
        Button("View all assignments", list_page),
        Button("Summary", summary_page),
        Button("Settings", settings_page),
    ])


@route
def add_page(state: State) -> Page:
    """Form for entering a new assignment."""
    return Page(state, [
        Header("Add an assignment", 1),
        "Title",
        TextBox("title", ""),
        "Course",
        SelectBox("course", COURSES),
        "Due date (YYYY-MM-DD)",
        TextBox("due_date", get_today()),
        "Hours estimated",
        TextBox("hours", "1"),
        CheckBox("high_priority", False),
        "High priority",
        Button("Submit", add_assignment),
        Button("Home", index),
    ])


@route
def add_assignment(state: State, title: str, course: str, due_date: str,
                   hours: str, high_priority: bool) -> Page:
    """Check the form, then add the new assignment to the list."""
    error = check_new_assignment(state.assignments, title, due_date, hours)
    if error != "":
        return Page(state, [
            Header("Could not add that assignment", 1),
            error,
            Button("Try again", add_page),
            Button("Home", index),
        ])
    state.assignments.append(Assignment(title.strip(), course,
                                        due_date.strip(), float(hours),
                                        high_priority, False))
    return list_page(state)


@route
def list_page(state: State) -> Page:
    """Show assignments (earliest due first) for the chosen course."""
    today = get_today()
    rows = []
    for assignment in sort_by_due_date(state.assignments):
        if matches_filter(assignment, state.current_filter):
            rows.append(make_table_row(assignment, today))
    content = [
        Header("All assignments", 1),
        "Show course:",
        SelectBox("course", [ALL_COURSES] + COURSES, state.current_filter),
        Button("Apply filter", set_filter),
    ]
    if len(rows) == 0:
        content.append("No assignments to show.")
    else:
        content.append(Table(rows, header=["Title", "Course", "Due",
                                           "Hours", "Status", ""]))
    content.append(Button("Home", index))
    return Page(state, content)


@route
def set_filter(state: State, course: str) -> Page:
    """Remember which course the list should show."""
    state.current_filter = course
    return list_page(state)


@route
def mark_done(state: State, title: str) -> Page:
    """Mark one assignment as finished and count it."""
    position = find_assignment_index(state.assignments, title)
    if position != -1 and not state.assignments[position].done:
        state.assignments[position].done = True
        state.total_completed += 1
    return list_page(state)


@route
def summary_page(state: State) -> Page:
    """Totals for the whole list: hours left, to-do count, overdue, done."""
    total = len(state.assignments)
    to_do = total - count_done(state.assignments)
    content = [
        Header("Summary", 1),
        f"Hours of work left: "
        f"{format_hours(total_hours_remaining(state.assignments))}",
        f"Assignments still to do: {to_do}",
        f"Overdue: {count_overdue(state.assignments, get_today())}",
        f"Finished: {state.total_completed} of {total}",
    ]
    if total > 0:
        content.append(ProgressBar(state.total_completed, total))
    content.append(Button("Home", index))
    return Page(state, content)


@route
def settings_page(state: State) -> Page:
    """Form for changing the name shown on the dashboard."""
    return Page(state, [
        Header("Settings", 1),
        "Your name",
        TextBox("new_name", state.username),
        Button("Save", save_settings),
        Button("Home", index),
    ])


@route
def save_settings(state: State, new_name: str) -> Page:
    """Save the new name (a blank name is ignored) and go home."""
    if new_name.strip() != "":
        state.username = new_name.strip()
    return index(state)


set_website_title("Assignment Tracker")
set_site_information(
    author="Quinn Doyen",
    description="Track assignments, due dates, and hours of work left.",
    sources=["Drafter documentation"],
    planning="planning_document.pdf",
    links=["https://github.com/YOUR-USERNAME/YOUR-REPOSITORY"],
)
start_server(State([], DEFAULT_USERNAME, ALL_COURSES, 0))


