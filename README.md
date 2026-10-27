# Pronote Organizer

Pronote Organizer is a local dashboard for your Pronote timetable, homework, and grades. It exports your schedule as an iCalendar (`.ics`) file and lets you download homework and grades as CSV files.

## Requirements

- Python 3.9 or later
- A Pronote account accessible through the URL configured in `fetch_schedule.py`

## Installation

Clone the repository and move into its directory:

```bash
git clone https://github.com/mehdi-bakkali/Pronote-Organizer.git
cd Pronote-Organizer
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Pronote credentials

The repository includes a `.env` file with blank username and password fields. Enter your own credentials locally:

```dotenv
PRONOTE_USERNAME=your_username
PRONOTE_PASSWORD=your_password
```

Never commit real credentials or share a `.env` file containing them. The values in the repository are blank so each user can add their own credentials after cloning.

## Usage

### Web interface

```bash
python web_server.py
```

Open [http://localhost:5001](http://localhost:5001) in your browser. The dashboard lets you configure the calendar export, preview upcoming lessons, and download homework and grades as CSV files. Stop the server with `Ctrl+C`.

Homework exports include items due from today through the end of the school year. Grades exports include all available school periods.

### Command line

```bash
python fetch_schedule.py --once      # Export the calendar using saved settings
python fetch_schedule.py --auto      # Export today's schedule
python fetch_schedule.py --homework  # Export homework to pronote_homework.csv
python fetch_schedule.py --grades    # Export grades to pronote_grades.csv
python fetch_schedule.py --config    # Edit the configuration in the terminal
python fetch_schedule.py --help      # Show help
```

With no option, the script starts in interactive mode. By default, the calendar is saved as `timetable.ics`. Import it into your calendar application.

## Configuration

Edit `config.json` to change the export settings. You can also change these settings in the web interface.

| Option | Description |
| --- | --- |
| `ics_output_path` | Path and filename for the generated calendar file. |
| `start_date` | First day to include, in `YYYY-MM-DD` format. |
| `days_ahead` | Number of days to include, starting from `start_date`. |
| `auto_refresh` | Set to `true` to refresh the calendar hourly while the web server is running. |
| `calendar_name` | Name displayed for the calendar in calendar apps. |
| `include_teacher` | Set to `true` to include teacher names in events. |
| `include_classroom` | Set to `true` to include classroom information in events. |

Keep the JSON syntax valid: use double quotes around option names and text values, and do not add a comma after the final option.
