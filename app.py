"""JobTrack: a simple job application tracker built with Flask and MySQL."""
from datetime import date, datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from mysql.connector import Error as MySQLError

import db
from config import Config

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY  # needed for flash messages

# The only four statuses allowed (they match the ENUM in schema.sql)
STATUSES = ["Applied", "Interview", "Offer", "Rejected"]


# ---------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------
def check_form(form):
    """Clean the submitted form and check it.

    Returns (values, errors):
      values - the cleaned text (used to refill the form if there are errors)
      errors - a list of messages to show the user (empty list = all good)
    """
    values = {
        "company_name": " ".join(form.get("company_name", "").split()),
        "job_title": " ".join(form.get("job_title", "").split()),
        "location": " ".join(form.get("location", "").split()),
        "job_link": form.get("job_link", "").strip(),
        "application_date": form.get("application_date", "").strip(),
        "status": form.get("status", "Applied"),
        "notes": form.get("notes", "").strip(),
    }
    errors = []

    # Company name: required, max 100 characters
    if not values["company_name"]:
        errors.append("Company name is required.")
    elif len(values["company_name"]) > 100:
        errors.append("Company name must be 100 characters or fewer.")

    # Job title: required, max 100 characters
    if not values["job_title"]:
        errors.append("Job title is required.")
    elif len(values["job_title"]) > 100:
        errors.append("Job title must be 100 characters or fewer.")

    # Location: optional, max 100 characters
    if len(values["location"]) > 100:
        errors.append("Location must be 100 characters or fewer.")

    # Job link: optional, but if given it must be a web address
    if values["job_link"]:
        if len(values["job_link"]) > 500:
            errors.append("Job link must be 500 characters or fewer.")
        elif not values["job_link"].lower().startswith(("http://", "https://")):
            errors.append("Job link must start with http:// or https://")

    # Application date: required, real date, not in the future
    if not values["application_date"]:
        errors.append("Application date is required.")
    else:
        try:
            applied_on = datetime.strptime(values["application_date"], "%Y-%m-%d").date()
            if applied_on > date.today():
                errors.append("Application date cannot be in the future.")
        except ValueError:
            errors.append("Application date is not a valid date.")

    # Status: must be one of the four allowed values
    if values["status"] not in STATUSES:
        errors.append("Status must be Applied, Interview, Offer or Rejected.")

    # Notes: optional, max 2000 characters
    if len(values["notes"]) > 2000:
        errors.append("Notes must be 2000 characters or fewer.")

    return values, errors


def get_application_or_404(application_id):
    """Return one application, or show the 'not found' page if it does not exist."""
    application = db.fetch_one(
        "SELECT * FROM applications WHERE application_id = %s", (application_id,)
    )
    if application is None:
        abort(404)
    return application


def row_to_form(application):
    """Turn a database row into the plain-text values the form needs."""
    return {
        "company_name": application["company_name"],
        "job_title": application["job_title"],
        "location": application["location"] or "",
        "job_link": application["job_link"] or "",
        "application_date": application["application_date"].isoformat(),  # YYYY-MM-DD
        "status": application["status"],
        "notes": application["notes"] or "",
    }


def show_form(form, errors, mode):
    """Show the add/edit form. mode is 'add' or 'edit'."""
    return render_template(
        "application_form.html",
        form=form,
        errors=errors,
        mode=mode,
        statuses=STATUSES,
        max_date=date.today().isoformat(),  # stops the date picker going past today
    )


# ---------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------
@app.route("/")
def dashboard():
    # One query counts everything. COALESCE turns "nothing" into 0 for an empty table.
    counts = db.fetch_one(
        """
        SELECT COUNT(*) AS total,
               COALESCE(SUM(status = 'Applied'), 0)   AS applied,
               COALESCE(SUM(status = 'Interview'), 0) AS interview,
               COALESCE(SUM(status = 'Offer'), 0)     AS offer,
               COALESCE(SUM(status = 'Rejected'), 0)  AS rejected
        FROM applications
        """
    )

    # The 5 most recent applications
    recent = db.fetch_all(
        """
        SELECT application_id, company_name, job_title, application_date, status
        FROM applications
        ORDER BY application_date DESC, application_id DESC
        LIMIT 5
        """
    )

    return render_template(
        "dashboard.html",
        total=int(counts["total"]),
        applied=int(counts["applied"]),
        interview=int(counts["interview"]),
        offer=int(counts["offer"]),
        rejected=int(counts["rejected"]),
        recent=recent,
        today=date.today(),
    )


# ---------------------------------------------------------------
# View all applications (with search)
# ---------------------------------------------------------------
@app.route("/applications")
def list_applications():
    search = request.args.get("search", "").strip()

    sql = """
        SELECT application_id, company_name, job_title, location,
               job_link, application_date, status, notes
        FROM applications
    """
    params = ()

    if search:
        # Only fixed text is added to the SQL. The user's search goes in params.
        sql += " WHERE company_name LIKE %s OR job_title LIKE %s"
        like_text = f"%{search}%"
        params = (like_text, like_text)

    sql += " ORDER BY application_date DESC, application_id DESC"

    applications = db.fetch_all(sql, params)
    return render_template(
        "applications.html",
        applications=applications,
        search=search,
        statuses=STATUSES,
    )


# ---------------------------------------------------------------
# Add an application
# ---------------------------------------------------------------
@app.route("/applications/add", methods=["GET", "POST"])
def add_application():
    if request.method == "POST":
        values, errors = check_form(request.form)

        if not errors:
            db.execute(
                """
                INSERT INTO applications
                    (company_name, job_title, location, job_link,
                     application_date, status, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    values["company_name"],
                    values["job_title"],
                    values["location"] or None,   # empty text is saved as NULL
                    values["job_link"] or None,
                    values["application_date"],
                    values["status"],
                    values["notes"] or None,
                ),
            )
            flash("Application added successfully.", "success")
            return redirect(url_for("list_applications"))

        # Errors found: show the form again with what the user typed
        return show_form(values, errors, "add")

    # First visit (GET): empty form, today's date, status Applied
    starting_values = {
        "application_date": date.today().isoformat(),
        "status": "Applied",
    }
    return show_form(starting_values, [], "add")


# ---------------------------------------------------------------
# Edit an application
# ---------------------------------------------------------------
@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
def edit_application(application_id):
    application = get_application_or_404(application_id)

    if request.method == "POST":
        values, errors = check_form(request.form)

        if not errors:
            db.execute(
                """
                UPDATE applications
                SET company_name = %s, job_title = %s, location = %s,
                    job_link = %s, application_date = %s, status = %s, notes = %s
                WHERE application_id = %s
                """,
                (
                    values["company_name"],
                    values["job_title"],
                    values["location"] or None,
                    values["job_link"] or None,
                    values["application_date"],
                    values["status"],
                    values["notes"] or None,
                    application_id,
                ),
            )
            flash("Application updated successfully.", "success")
            return redirect(url_for("list_applications"))

        return show_form(values, errors, "edit")

    # First visit (GET): fill the form with the saved values
    return show_form(row_to_form(application), [], "edit")


# ---------------------------------------------------------------
# Change status (the dropdown in the applications table)
# ---------------------------------------------------------------
@app.route("/applications/<int:application_id>/status", methods=["POST"])
def update_status(application_id):
    get_application_or_404(application_id)

    new_status = request.form.get("status", "")
    search = request.form.get("search", "").strip()  # keeps the search on screen

    if new_status not in STATUSES:
        flash("That status is not valid.", "danger")
    else:
        db.execute(
            "UPDATE applications SET status = %s WHERE application_id = %s",
            (new_status, application_id),
        )
        flash(f"Status changed to {new_status}.", "success")

    return redirect(url_for("list_applications", search=search or None))


# ---------------------------------------------------------------
# Delete an application (the confirmation popup is in the template)
# ---------------------------------------------------------------
@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):
    get_application_or_404(application_id)
    search = request.form.get("search", "").strip()

    db.execute("DELETE FROM applications WHERE application_id = %s", (application_id,))
    flash("Application deleted.", "success")

    return redirect(url_for("list_applications", search=search or None))


# ---------------------------------------------------------------
# Error pages
# ---------------------------------------------------------------
@app.errorhandler(MySQLError)
def handle_database_error(error):
    # The technical details go to the terminal, not to the visitor.
    app.logger.error("Database error: %s", error)
    return (
        render_template(
            "error.html",
            title="Database problem",
            message="Something went wrong talking to the database. "
                    "Check that MySQL is running and that your .env settings are correct.",
        ),
        500,
    )


@app.errorhandler(404)
def handle_not_found(error):
    return (
        render_template(
            "error.html",
            title="Page not found",
            message="The page or application you asked for does not exist.",
        ),
        404,
    )


if __name__ == "__main__":
    # debug=True is for learning on your own computer only.
    app.run(debug=True)