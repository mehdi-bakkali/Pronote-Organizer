# Pronote Schedule Exporter

This project retrieves lessons from a Pronote account and exports them to an iCalendar (`.ics`) file. It also provides a local web interface for configuring the export and refreshing the calendar.

## Requirements

- Python 3.9 or later
- A Pronote account accessible through the URL configured in `fetch_schedule.py`

## Installation

Clone the repository and move into its directory:

```bash
git clone <https://github.com/mehdi-bakkali/Pronote-Calendar-exporter>
cd pronote
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

The project includes a `.env` file in its root directory. Open it and enter your Pronote username and password on these two lines:

```dotenv
PRONOTE_USERNAME=your_username
PRONOTE_PASSWORD=your_password
```

Do not commit real credentials to a public repository. If you plan to publish this project, leave these values blank before pushing and enter your credentials locally afterward.

## Usage

### Web interface

```bash
python web_server.py
```

Open [http://localhost:5001](http://localhost:5001) in your browser. The interface lets you configure the date range, calendar name, whether to include teachers and classrooms, and automatic refresh. Stop the server with `Ctrl+C`.

### Command line

```bash
python fetch_schedule.py --once   # Export using the saved configuration
python fetch_schedule.py --auto   # Export today's schedule
python fetch_schedule.py --config # Edit the configuration in the terminal
python fetch_schedule.py --help   # Show help
```

With no option, the script starts in interactive mode. By default, the output is saved as `timetable.ics`. Import the file into, or subscribe to it from, your calendar application.

## Configuration

The project includes `config.json`, which stores the export settings. Edit this file with any text editor, then save it before running the exporter. The web interface can also update these settings for you.

Available options:

| Option | Description |
| --- | --- |
| `ics_output_path` | Path and filename for the generated calendar file. |
| `start_date` | First day to include, in `YYYY-MM-DD` format. |
| `days_ahead` | Number of days to include, starting from `start_date`. |
| `auto_refresh` | Set to `true` to enable automatic refresh in the web server, or `false` to disable it. |
| `calendar_name` | Name displayed for the calendar in calendar apps. |
| `include_teacher` | Set to `true` to include teacher names in events. |
| `include_classroom` | Set to `true` to include classroom information in events. |

Keep the JSON syntax valid: use double quotes around option names and text values, and do not add a comma after the final option. If an option is missing, the program fills it with its default value.

## Dependencies

Required libraries are listed in [`requirements.txt`](requirements.txt).
# Pronote-Calendar-exporter
