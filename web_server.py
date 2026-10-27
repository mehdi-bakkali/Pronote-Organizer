

import os
import json
import io
import webbrowser
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from fetch_schedule import (
    load_config,
    save_config,
    run_export,
    DEFAULT_CONFIG,
    authenticate,
    fetch_daily_schedule,
    extract_lesson_data,
    create_ics_calendar,
    homework_to_csv,
    grades_to_csv,
)

app = Flask(__name__)
app.secret_key = "pronote-secret-key-change-in-production"
app.config["JSON_SORT_KEYS"] = False

CONFIG_FILE = "config.json"

scheduler = BackgroundScheduler()
scheduler.start()


def get_config():
    """Load current configuration."""
    return load_config()


def auto_update_ics():
    """Automatically update the ICS file with today's schedule."""
    try:
        config = load_config()
        if not config.get("auto_refresh", False):
            return

        print("[Auto-Update] Generating ICS file...")
        config["start_date"] = datetime.now().strftime("%Y-%m-%d")
        config["days_ahead"] = config.get("days_ahead", 7)

        pron = authenticate()
        start_date = datetime.strptime(config["start_date"], "%Y-%m-%d").date()
        lessons = fetch_daily_schedule(pron, start_date, config["days_ahead"])

        if lessons:
            lesson_data_list = [extract_lesson_data(lesson, config) for lesson in lessons]
            cal = create_ics_calendar(lesson_data_list, config)

            output_file = config.get("ics_output_path", "timetable.ics")
            with open(output_file, "wb") as f:
                f.write(cal.to_ical())

            print(f"[Auto-Update] Successfully exported {len(lesson_data_list)} lessons to '{output_file}'")
        else:
            print("[Auto-Update] No lessons found")
    except Exception as e:
        print(f"[Auto-Update] Error: {e}")


@app.route("/")
def index():
    """Display the configuration interface."""
    config = get_config()
    return render_template("config.html", config=config, defaults=DEFAULT_CONFIG)


@app.route("/save", methods=["POST"])
def save_configuration():
    """Save configuration from web form."""
    config = {
        "ics_output_path": request.form.get("ics_output_path", "timetable.ics"),
        "start_date": request.form.get("start_date", datetime.now().strftime("%Y-%m-%d")),
        "days_ahead": int(request.form.get("days_ahead", 1)),
        "auto_refresh": request.form.get("auto_refresh") == "on",
        "calendar_name": request.form.get("calendar_name", "My Pron Schedule"),
        "include_teacher": request.form.get("include_teacher") == "on",
        "include_classroom": request.form.get("include_classroom") == "on",
    }

    save_config(config)

    # Update scheduler based on auto_refresh setting
    if config.get("auto_refresh"):
        scheduler.add_job(auto_update_ics, IntervalTrigger(hours=1), id="auto_update", replace_existing=True)
        flash("Configuration saved! Auto-update enabled (runs every hour)", "success")
    else:
        scheduler.remove_job("auto_update") if scheduler.get_job("auto_update") else None
        flash("Configuration saved! Auto-update disabled", "success")

    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset_defaults():
    """Reset configuration to defaults."""
    save_config(DEFAULT_CONFIG.copy())
    flash("Configuration reset to defaults!", "info")
    return redirect(url_for("index"))


@app.route("/generate", methods=["POST"])
def generate_ics():
    """Manually trigger ICS file generation."""
    try:
        config = get_config()
        output_file = run_export(config)
        flash(f"ICS file generated successfully: {output_file}", "success")
    except Exception as e:
        flash(f"Error generating ICS: {str(e)}", "error")
    return redirect(url_for("index"))


def create_csv_download(filename, csv_text):
    """Build a UTF-8 CSV download that opens cleanly in spreadsheet apps."""
    content = io.BytesIO(csv_text.encode("utf-8-sig"))
    return send_file(
        content,
        mimetype="text/csv; charset=utf-8",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/export/homework.csv")
def export_homework_csv():
    """Download homework from today through the end of the school year."""
    try:
        pron = authenticate()
        return create_csv_download("pronote_homework.csv", homework_to_csv(pron))
    except Exception as error:
        flash(f"Could not export homework: {error}", "error")
        return redirect(url_for("index"))


@app.route("/export/grades.csv")
def export_grades_csv():
    """Download grades from every available school period."""
    try:
        pron = authenticate()
        return create_csv_download("pronote_grades.csv", grades_to_csv(pron))
    except Exception as error:
        flash(f"Could not export grades: {error}", "error")
        return redirect(url_for("index"))


@app.route("/api/status")
def api_status():
    """Return current configuration and ICS file status."""
    config = get_config()
    ics_path = config.get("ics_output_path", "timetable.ics")
    ics_exists = os.path.exists(ics_path)
    ics_mtime = None
    if ics_exists:
        mtime = os.path.getmtime(ics_path)
        ics_mtime = datetime.fromtimestamp(mtime).isoformat()

    return jsonify({
        "config": config,
        "ics_file": {
            "path": ics_path,
            "exists": ics_exists,
            "last_modified": ics_mtime,
        }
    })


@app.route("/api/update", methods=["POST"])
def api_update():
    """API endpoint to trigger ICS update."""
    try:
        config = get_config()
        # Always use today's date for auto updates
        config["start_date"] = datetime.now().strftime("%Y-%m-%d")
        config["days_ahead"] = 7  # Default to 7 days ahead

        output_file = run_export(config)

        return jsonify({
            "success": True,
            "message": f"Generated {output_file}",
            "lessons_count": len(config.get("_lesson_count", 0)),
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/preview")
def api_preview():
    """Preview upcoming lessons without generating ICS."""
    try:
        config = get_config()
        pron = authenticate()

        start_date = datetime.strptime(config["start_date"], "%Y-%m-%d").date()
        days_ahead = config.get("days_ahead", 7)

        lessons = fetch_daily_schedule(pron, start_date, days_ahead)

        preview = []
        for lesson in lessons:
            data = extract_lesson_data(lesson, config)
            preview.append({
                "subject": data["subject_name"],
                "start": data["start_time"].strftime("%Y-%m-%d %H:%M"),
                "end": data["end_time"].strftime("%Y-%m-%d %H:%M"),
                "classroom": data["classroom"] or "N/A",
                "teacher": data["teacher"] or "N/A",
            })

        return jsonify({"lessons": preview})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def open_browser():
    """Open browser after server starts."""
    webbrowser.open("http://localhost:5001")


if __name__ == "__main__":
    print("=" * 60)
    print("Pronote Web Configuration Interface")
    print("=" * 60)
    print("Starting server at http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Start auto-update scheduler if enabled in config
    config = get_config()
    if config.get("auto_refresh", False):
        scheduler.add_job(auto_update_ics, IntervalTrigger(hours=1), id="auto_update", replace_existing=True)
        print("Auto-update scheduler started (runs every hour)")
    else:
        print("Auto-update disabled in configuration")

    # Open browser after 1 second delay
    import threading
    threading.Timer(1.0, open_browser).start()

    app.run(host="0.0.0.0", port=5001, debug=True)
