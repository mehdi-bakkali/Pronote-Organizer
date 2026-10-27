"""
Pronote Organizer: export your timetable, homework, and grades.
Includes a local configuration interface and calendar automation.
"""

import os
import json
import sys
import csv
import io
from datetime import date, datetime, timedelta
from icalendar import Calendar, Event

import dotenv
from pronotepy import Client

# Default configuration
DEFAULT_CONFIG = {
    "ics_output_path": "timetable.ics",
    "start_date": "2025-03-16",
    "days_ahead": 1,
    "auto_refresh": True,
    "calendar_name": "My Pron Schedule",
    "include_teacher": True,
    "include_classroom": True,
}

CONFIG_FILE = "config.json"


def load_config():
    """Load configuration from config.json or create default."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        # Merge with defaults for any missing keys
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
        return config
    else:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def show_config_menu():
    """Display interactive configuration menu."""
    config = load_config()

    print("\n" + "=" * 60)
    print("CONFIGURATION MENU")
    print("=" * 60)
    print("\nCurrent settings:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    print("\nOptions:")
    print("  1. Change ICS output file path")
    print("  2. Change start date")
    print("  3. Change days ahead (how many days to fetch)")
    print("  4. Toggle auto-refresh")
    print("  5. Change calendar name")
    print("  6. Toggle include teacher names")
    print("  7. Toggle include classroom")
    print("  8. Reset to defaults")
    print("  9. Save and exit")
    print("  0. Exit without saving")

    while True:
        choice = input("\nEnter option (0-9): ").strip()

        if choice == "1":
            new_path = input(f"New ICS path [{config['ics_output_path']}]: ").strip()
            if new_path:
                config["ics_output_path"] = new_path
        elif choice == "2":
            new_date = input(f"New start date [{config['start_date']}]: ").strip()
            if new_date:
                config["start_date"] = new_date
        elif choice == "3":
            new_days = input(f"Days ahead [{config['days_ahead']}]: ").strip()
            if new_days and new_days.isdigit():
                config["days_ahead"] = int(new_days)
        elif choice == "4":
            config["auto_refresh"] = not config["auto_refresh"]
            print(f"  Auto-refresh set to: {config['auto_refresh']}")
        elif choice == "5":
            new_name = input(f"Calendar name [{config['calendar_name']}]: ").strip()
            if new_name:
                config["calendar_name"] = new_name
        elif choice == "6":
            config["include_teacher"] = not config["include_teacher"]
            print(f"  Include teacher set to: {config['include_teacher']}")
        elif choice == "7":
            config["include_classroom"] = not config["include_classroom"]
            print(f"  Include classroom set to: {config['include_classroom']}")
        elif choice == "8":
            config = DEFAULT_CONFIG.copy()
            print("  Reset to defaults!")
        elif choice == "9":
            save_config(config)
            print("  Configuration saved!")
            return config
        elif choice == "0":
            print("  Exiting without saving...")
            return None
        else:
            print("  Invalid option, try again.")


def load_credentials():
    """Load credentials from .env file."""
    dotenv.load_dotenv()

    username = os.getenv("PRONOTE_USERNAME")
    password = os.getenv("PRONOTE_PASSWORD")

    if not username or not password:
        print("Error: Please set PRONOTE_USERNAME and PRONOTE_PASSWORD in .env file")
        print("Example .env content:")
        print("PRONOTE_USERNAME=your_username_here")
        print("PRONOTE_PASSWORD=your_password_here")
        sys.exit(1)

    return username, password


def authenticate():
    """Authenticate with Pron."""
    username, password = load_credentials()
    url = "https://1000168p.index-education.net/pronote/eleve.html"

    print("Connecting to Pron...")
    try:
        pron = Client(url, username, password)
        print(f"Successfully authenticated as {username}")
        return pron
    except Exception as e:
        print(f"Login error: {e}")
        raise Exception("Authentication failed. Please check your credentials.")


def fetch_daily_schedule(pron, start_date, days_ahead):
    """
    Fetch lessons for specified date range from Pron.
    """
    print(f"Fetching schedule from {start_date} for {days_ahead} day(s)...")

    lessons = pron.lessons(start_date, start_date + timedelta(days=days_ahead))

    if not lessons:
        print("No lessons found.")
        return []

    print(f"Found {len(lessons)} lessons.")
    return lessons


def extract_lesson_data(lesson, config):
    """
    Extract relevant data from a Pron lesson.
    """
    subject = lesson.subject
    subject_name = subject.name if subject else "No Subject"

    start = lesson.start
    end = lesson.end

    start_dt = start
    end_dt = end

    duration = timedelta(minutes=int((end_dt - start_dt).total_seconds() / 60))

    teacher_name = ""
    if config.get("include_teacher", True) and lesson.teacher_names:
        teacher_name = ", ".join(lesson.teacher_names)

    classroom = ""
    if config.get("include_classroom", True) and lesson.classrooms:
        classroom = ", ".join(lesson.classrooms)

    return {
        "subject_name": subject_name,
        "start_time": start_dt,
        "end_time": end_dt,
        "duration": duration,
        "classroom": classroom,
        "teacher": teacher_name
    }


def create_ics_calendar(lessons, config):
    """
    Create an ICS calendar from the list of lessons.
    """
    cal = Calendar()
    cal.add("PRODID", "-//Pronote Organizer//NONSGML//EN")
    cal.add("VERSION", "2.0")
    cal.add("CALSCALE", "GREGORIAN")
    cal.add("METHOD", "PUBLISH")
    cal.add("X-WR-CALNAME", config.get("calendar_name", "My Pron Schedule"))

    cal_description = f"Schedule exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    cal.add("DESCRIPTION", cal_description)

    for lesson_data in lessons:
        event = Event()
        event.add("summary", lesson_data["subject_name"])
        event.add("dtstart", lesson_data["start_time"])
        event.add("dtend", lesson_data["end_time"])

        description_parts = []
        if lesson_data["classroom"]:
            description_parts.append(f"Location: {lesson_data['classroom']}")
        if lesson_data["teacher"]:
            description_parts.append(f"Teacher: {lesson_data['teacher']}")

        event.add("description", " | ".join(description_parts))
        event.add("uid", f"{lesson_data['subject_name']}{lesson_data['start_time'].strftime('%Y%m%d%H%M')}@pron")

        cal.add_component(event)

    return cal


def run_export(config=None):
    """Run the schedule export process."""
    if config is None:
        config = load_config()

    print("=" * 60)
    print("Pronote Organizer | Timetable Calendar Export")
    print("=" * 60)
    print()

    # Parse start date
    try:
        start_date = datetime.strptime(config["start_date"], "%Y-%m-%d").date()
    except ValueError:
        print(f"Invalid start_date format: {config['start_date']}. Use YYYY-MM-DD.")
        return

    days_ahead = config.get("days_ahead", 1)

    # Authenticate
    try:
        pron = authenticate()
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    # Fetch schedule
    lessons = fetch_daily_schedule(pron, start_date, days_ahead)

    if not lessons:
        print("No lessons found to export.")
        return

    # Extract lesson data
    print("\nExtracting lesson details...")
    lesson_data_list = []
    for lesson in lessons:
        data = extract_lesson_data(lesson, config)
        lesson_data_list.append(data)
        print(f"  - {data['subject_name']} ({data['classroom'] or 'N/A'})")

    # Create ICS calendar
    print("\nCreating ICS calendar...")
    cal = create_ics_calendar(lesson_data_list, config)

    # Save to file
    output_file = config.get("ics_output_path", "timetable.ics")
    with open(output_file, "wb") as f:
        f.write(cal.to_ical())

    print(f"\n{'=' * 60}")
    print(f"SUCCESS: {len(lesson_data_list)} lessons exported to '{output_file}'")
    print(f"{'=' * 60}")

    print("\nExported lessons:")
    for i, data in enumerate(lesson_data_list, 1):
        print(f"  {i}. {data['subject_name']}")
        print(f"     Time: {data['start_time'].strftime('%H:%M')} - {data['end_time'].strftime('%H:%M')}")
        print(f"     {data['classroom'] or 'N/A'} | {data['teacher'] or 'N/A'}")
        print()

    return output_file


def _csv_content(headers, rows):
    """Serialize rows to CSV text for downloads and local exports."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()


def homework_to_csv(pron, date_from=None, date_to=None):
    """Return homework from date_from through date_to as CSV text.

    When no dates are provided, this exports homework from today through the
    end of the school year.
    """
    homework_items = pron.homework(date_from or date.today(), date_to)
    rows = []
    for item in homework_items:
        subject = getattr(item, "subject", None)
        due_date = getattr(item, "date", None)
        rows.append([
            due_date.isoformat() if due_date else "",
            getattr(subject, "name", "") if subject else "",
            getattr(item, "description", "") or "",
            "Done" if getattr(item, "done", False) else "To do",
        ])
    return _csv_content(["Due date", "Subject", "Description", "Status"], rows)


def grades_to_csv(pron):
    """Return grades from every available school period as CSV text."""
    rows = []
    for period in pron.periods:
        for grade in period.grades:
            subject = getattr(grade, "subject", None)
            grade_date = getattr(grade, "date", None)
            rows.append([
                getattr(period, "name", "") or "",
                grade_date.isoformat() if grade_date else "",
                getattr(subject, "name", "") if subject else "",
                getattr(grade, "grade", "") or "",
                getattr(grade, "out_of", "") or "",
                getattr(grade, "coefficient", "") or "",
                getattr(grade, "average", "") or "",
                getattr(grade, "comment", "") or "",
            ])
    return _csv_content(
        ["Period", "Date", "Subject", "Grade", "Out of", "Coefficient", "Class average", "Comment"],
        rows,
    )


def run_homework_export(output_file="pronote_homework.csv"):
    """Fetch homework and write it to a CSV file."""
    try:
        content = homework_to_csv(authenticate())
        with open(output_file, "w", encoding="utf-8-sig", newline="") as file:
            file.write(content)
        print(f"Homework exported to '{output_file}'")
        return output_file
    except Exception as error:
        print(f"Homework export failed: {error}")
        return None


def run_grades_export(output_file="pronote_grades.csv"):
    """Fetch grades and write them to a CSV file."""
    try:
        content = grades_to_csv(authenticate())
        with open(output_file, "w", encoding="utf-8-sig", newline="") as file:
            file.write(content)
        print(f"Grades exported to '{output_file}'")
        return output_file
    except Exception as error:
        print(f"Grades export failed: {error}")
        return None


def setup_daily_task():
    """Create a Windows Task Scheduler task for daily execution."""
    import subprocess

    script_path = os.path.abspath(__file__)
    task_name = "PronScheduleDaily"

    # Create schtasks command
    cmd = f'schtasks /Create /TN "{task_name}" /TR "python \"{script_path}\" --auto" /SC DAILY /ST 06:00 /F'

    print(f"Creating scheduled task: {task_name}")
    print(f"Command: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("Scheduled task created successfully!")
            print("The script will run daily at 6:00 AM.")
        else:
            print(f"Failed to create task: {result.stderr}")
    except Exception as e:
        print(f"Error creating task: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--auto":
            # Auto mode: fetch today's schedule (for daily automation)
            config = load_config()
            config["start_date"] = datetime.now().strftime("%Y-%m-%d")
            config["days_ahead"] = 1  # Just today
            run_export(config)
        elif sys.argv[1] == "--config":
            show_config_menu()
        elif sys.argv[1] == "--schedule":
            setup_daily_task()
        elif sys.argv[1] == "--once":
            # One-time run with configured date
            config = load_config()
            run_export(config)
        elif sys.argv[1] == "--homework":
            run_homework_export()
        elif sys.argv[1] == "--grades":
            run_grades_export()
        elif sys.argv[1] == "--help":
            print("Usage: python fetch_schedule.py [OPTIONS]")
            print()
            print("Options:")
            print("  --auto      Fetch today's schedule (for daily automation)")
            print("  --once      Run once with configured start_date")
            print("  --config    Open configuration menu")
            print("  --homework  Export homework to CSV")
            print("  --grades    Export grades to CSV")
            print("  --schedule  Set up daily Windows Task Scheduler task")
            print("  --help      Show this help message")
            print()
            print("Without options, runs in interactive mode.")
    else:
        # Interactive mode
        print("=" * 60)
        print("Pronote Organizer - Interactive Mode")
        print("=" * 60)
        print("\nStarting on March 16, 2025 (or configured date)")
        print("Daily automation available\n")

        config = show_config_menu()
        if config:
            run_export(config)
            print("\nTip: Run 'python fetch_schedule.py --schedule' to set up daily automation")


if __name__ == "__main__":
    main()
