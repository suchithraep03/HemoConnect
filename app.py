
import os
import sqlite3
from datetime import timedelta
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from database import get_connection, initialize_database


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "hemoconnect-local-demo-key-change-before-deployment"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.permanent_session_lifetime = timedelta(days=30)


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

initialize_database()


# ---------------------------------------------------------
# FORM OPTIONS
# ---------------------------------------------------------

BLOOD_GROUPS = [
    "A+", "A-", "B+", "B-",
    "AB+", "AB-", "O+", "O-"
]

DEPARTMENTS = [
    "ECE",
    "CSE",
    "EEE",
    "ME",
    "CE",
    "ICE"
]

ACADEMIC_YEARS = [
    "First Year",
    "Second Year",
    "Third Year",
    "Fourth Year",
    "Faculty/Staff",
]

COMPONENTS = [
    "Red Blood Cells",
    "Platelets",
    "Plasma",
    "Whole Blood",
]

URGENCIES = [
    "Critical",
    "Urgent",
    "Normal",
]


# Simplified red blood cell compatibility.
# All real matches require blood-bank confirmation.
RBC_COMPATIBILITY = {
    "A+": ["A+", "A-", "O+", "O-"],
    "A-": ["A-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    "AB-": ["A-", "B-", "AB-", "O-"],
    "O+": ["O+", "O-"],
    "O-": ["O-"],
}


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "donor_id" not in session:
            return redirect(
                url_for(
                    "access_required",
                    next="request_blood"
                )
            )

        return function(*args, **kwargs)

    return wrapper


def get_logged_in_donor():
    donor_id = session.get("donor_id")

    if donor_id is None:
        return None

    connection = get_connection()

    try:
        return connection.execute(
            "SELECT * FROM donors WHERE id = ?",
            (donor_id,)
        ).fetchone()

    finally:
        connection.close()


def render_registration(error=None):
    return render_template(
        "register.html",
        blood_groups=BLOOD_GROUPS,
        departments=DEPARTMENTS,
        academic_years=ACADEMIC_YEARS,
        error=error,
    )


def render_request_form(error=None):
    return render_template(
        "request.html",
        blood_groups=BLOOD_GROUPS,
        components=COMPONENTS,
        urgencies=URGENCIES,
        error=error,
    )


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return redirect(url_for("home") + "#about")


@app.route("/features")
def features():
    return redirect(url_for("home") + "#features")


@app.route("/contact")
def contact():
    return redirect(url_for("home") + "#contact")


# ---------------------------------------------------------
# ACCESS REQUIRED
# ---------------------------------------------------------

@app.route("/access-required")
def access_required():

    if session.get("donor_id"):
        next_page = request.args.get(
            "next",
            "request_blood"
        )

        if next_page == "dashboard":
            return redirect(url_for("dashboard"))

        return redirect(url_for("request_blood"))

    next_page = request.args.get(
        "next",
        "request_blood"
    )

    if next_page not in ("request_blood", "dashboard"):
        next_page = "request_blood"

    return render_template(
        "access_required.html",
        next_page=next_page
    )


# ---------------------------------------------------------
# DONOR REGISTRATION
# ---------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if session.get("donor_id"):
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_registration()

    full_name = request.form.get(
        "full_name", ""
    ).strip()

    email = request.form.get(
        "email", ""
    ).strip().lower()

    phone = request.form.get(
        "phone", ""
    ).strip()

    blood_group = request.form.get(
        "blood_group", ""
    ).strip()

    department = request.form.get(
        "department", ""
    ).strip()

    academic_year = request.form.get(
        "academic_year", ""
    ).strip()

    last_donation_date = request.form.get(
        "last_donation_date", ""
    ).strip() or None

    location = request.form.get(
        "location", ""
    ).strip()

    consent = (
        1 if request.form.get("consent") == "yes"
        else 0
    )

    if not all([
        full_name,
        email,
        phone,
        blood_group,
        department,
        academic_year,
        location,
    ]):
        return render_registration(
            "Please complete all required fields."
        )

    if "@" not in email or "." not in email.split("@")[-1]:
        return render_registration(
            "Please enter a valid email address."
        )

    if blood_group not in BLOOD_GROUPS:
        return render_registration(
            "Please select a valid blood group."
        )

    if department not in DEPARTMENTS:
        return render_registration(
            "Please select a valid department."
        )

    if academic_year not in ACADEMIC_YEARS:
        return render_registration(
            "Please select a valid academic year."
        )

    if consent != 1:
        return render_registration(
            "Please provide consent before registering."
        )

    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO donors (
                full_name,
                email,
                phone,
                blood_group,
                department,
                academic_year,
                last_donation_date,
                location,
                available,
                consent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name,
            email,
            phone,
            blood_group,
            department,
            academic_year,
            last_donation_date,
            location,
            1,
            consent,
        ))

        connection.commit()

        donor = connection.execute(
            "SELECT id FROM donors WHERE email = ?",
            (email,)
        ).fetchone()

        session.clear()
        session["donor_id"] = donor["id"]
        session.permanent = True

        return redirect(url_for("dashboard"))

    except sqlite3.IntegrityError:
        return render_registration(
            "This email is already registered. Please log in."
        )

    finally:
        connection.close()


# ---------------------------------------------------------
# EMAIL-ONLY DEMONSTRATION LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("donor_id"):
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_template(
            "login.html",
            error=None
        )

    email = request.form.get(
        "email", ""
    ).strip().lower()

    if not email:
        return render_template(
            "login.html",
            error="Please enter your registered email."
        )

    connection = get_connection()

    try:
        donor = connection.execute(
            """
            SELECT id
            FROM donors
            WHERE LOWER(email) = ?
            """,
            (email,)
        ).fetchone()

    finally:
        connection.close()

    if donor is None:
        return render_template(
            "login.html",
            error="Email not found. Please register first."
        )

    session.clear()
    session["donor_id"] = donor["id"]
    session.permanent = True

    next_page = request.args.get(
        "next",
        request.form.get("next", "dashboard")
    )

    if next_page == "request_blood":
        return redirect(url_for("request_blood"))

    return redirect(url_for("dashboard"))


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    donor = get_logged_in_donor()

    if donor is None:
        session.clear()
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        donor=donor
    )


# ---------------------------------------------------------
# UPDATE AVAILABILITY
# ---------------------------------------------------------

@app.route("/toggle-availability", methods=["POST"])
@login_required
def toggle_availability():

    donor = get_logged_in_donor()

    if donor is None:
        session.clear()
        return redirect(url_for("login"))

    new_status = 0 if donor["available"] else 1

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE donors
            SET available = ?
            WHERE id = ?
            """,
            (new_status, donor["id"])
        )

        connection.commit()

    finally:
        connection.close()

    return redirect(url_for("dashboard"))


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------------------------------------------------
# BLOOD REQUEST FORM
# ---------------------------------------------------------

@app.route("/request-blood", methods=["GET", "POST"])
@login_required
def request_blood():

    donor = get_logged_in_donor()

    if donor is None:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_request_form()

    # Automatically use the logged-in user's registered email.
    requester_email = donor["email"]

    requester_name = request.form.get(
        "requester_name", ""
    ).strip()

    requester_phone = request.form.get(
        "requester_phone", ""
    ).strip()

    blood_group = request.form.get(
        "blood_group", ""
    ).strip()

    component = request.form.get(
        "component", ""
    ).strip()

    units_text = request.form.get(
        "units", ""
    ).strip()

    hospital_name = request.form.get(
        "hospital_name", ""
    ).strip()

    hospital_address = request.form.get(
        "hospital_address", ""
    ).strip()

    urgency = request.form.get(
        "urgency", ""
    ).strip()

    # Validate required fields.
    if not all([
        requester_name,
        requester_phone,
        blood_group,
        component,
        units_text,
        hospital_name,
        hospital_address,
        urgency,
    ]):
        return render_request_form(
            "Please complete all required fields."
        )

    if blood_group not in BLOOD_GROUPS:
        return render_request_form(
            "Please select a valid blood group."
        )

    if component not in COMPONENTS:
        return render_request_form(
            "Please select a valid blood component."
        )

    if urgency not in URGENCIES:
        return render_request_form(
            "Please select a valid urgency."
        )

    try:
        units = int(units_text)

        if not 1 <= units <= 100:
            raise ValueError

    except ValueError:
        return render_request_form(
            "Enter a valid quantity."
        )

    connection = get_connection()

    try:
        # Save the blood request.
        cursor = connection.execute("""
            INSERT INTO blood_requests (
                requester_name,
                requester_email,
                requester_phone,
                blood_group,
                component,
                units,
                hospital_name,
                hospital_address,
                urgency,
                status,
                requester_donor_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            requester_name,
            requester_email,
            requester_phone,
            blood_group,
            component,
            units,
            hospital_name,
            hospital_address,
            urgency,
            "Pending",
            donor["id"],
        ))

        request_id = cursor.lastrowid

                # Automated matching for all blood components.
        # This is a simplified educational demonstration only.

        if component in COMPONENTS:

            # Simplified RBC compatibility.
            if component == "Red Blood Cells":
                compatible_groups = RBC_COMPATIBILITY[blood_group]

            # For the demo, use same-blood-group matching for
            # Platelets, Plasma and Whole Blood.
            # Actual compatibility must be verified by a blood bank.
            else:
                compatible_groups = [blood_group]

            placeholders = ",".join(
                "?" for _ in compatible_groups
            )

            matches = connection.execute(
                f"""
                SELECT id
                FROM donors
                WHERE blood_group IN ({placeholders})
                  AND available = 1
                  AND consent = 1
                  AND id != ?
                ORDER BY
                    CASE
                        WHEN last_donation_date IS NULL
                             OR last_donation_date = ''
                        THEN 1
                        ELSE 0
                    END,
                    last_donation_date ASC,
                    academic_year ASC
                """,
                tuple(compatible_groups) + (donor["id"],)
            ).fetchall()

            # Save the matching donors.
            for matched_donor in matches:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO request_matches (
                        request_id,
                        donor_id,
                        donor_response
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        request_id,
                        matched_donor["id"],
                        "Awaiting Response",
                    )
                )

        connection.commit()

        # Redirect to the matching results page.
        return redirect(
            url_for(
                "request_results",
                request_id=request_id
            )
        )

    except sqlite3.Error:
        connection.rollback()

        app.logger.exception(
            "Database error while processing blood request"
        )

        return (
            "Unable to process the blood request. "
            "Check the VS Code terminal for the database error.",
            500
        )

    finally:
        connection.close()


# ---------------------------------------------------------
# MATCHING RESULTS
# ---------------------------------------------------------

@app.route("/request-results/<int:request_id>")
@login_required
def request_results(request_id):

    current_donor = get_logged_in_donor()

    if current_donor is None:
        session.clear()
        return redirect(url_for("login"))

    connection = get_connection()

    try:
        blood_request = connection.execute(
            """
            SELECT *
            FROM blood_requests
            WHERE id = ?
            """,
            (request_id,)
        ).fetchone()

        if blood_request is None:
            return "Blood request not found.", 404

        is_requester = (
            blood_request["requester_donor_id"]
            == current_donor["id"]
        )

        matches = connection.execute(
    """
    SELECT
        donors.id AS donor_id,
        donors.student_id,
        donors.full_name,
        donors.phone,
        donors.blood_group,
        donors.department,
        donors.academic_year,
        donors.location,
        donors.last_donation_date,
        donors.available,
        request_matches.id AS match_id,
        request_matches.donor_response
    FROM request_matches
    JOIN donors
        ON donors.id = request_matches.donor_id
    WHERE request_matches.request_id = ?
    ORDER BY donors.full_name ASC
    """,
    (request_id,)
).fetchall()

        # Only the requester and matched donors can see results.
        is_matched_donor = any(
            match["donor_id"] == current_donor["id"]
            for match in matches
        )

        if not is_requester and not is_matched_donor:
            return (
                "You are not authorized to view this request.",
                403
            )

        return render_template(
    "results.html",
    blood_request=blood_request,
    matches=matches,
    current_donor_id=current_donor["id"],
    is_requester=is_requester,
    academic_years=ACADEMIC_YEARS,
    departments=DEPARTMENTS
)

    finally:
        connection.close()


# ---------------------------------------------------------
# DONOR RESPONSE
# ---------------------------------------------------------

@app.route(
    "/match-response/<int:match_id>",
    methods=["POST"]
)
@login_required
def match_response(match_id):

    donor = get_logged_in_donor()

    if donor is None:
        session.clear()
        return redirect(url_for("login"))

    response_status = request.form.get(
        "response", ""
    ).strip()

    if response_status not in (
        "Available",
        "Unavailable"
    ):
        return "Invalid response.", 400

    connection = get_connection()

    try:
        match = connection.execute(
            """
            SELECT request_id, donor_id
            FROM request_matches
            WHERE id = ?
            """,
            (match_id,)
        ).fetchone()

        if match is None:
            return "Match not found.", 404

        # Donors can only respond to their own match.
        if match["donor_id"] != donor["id"]:
            return (
                "You cannot update another donor's response.",
                403
            )

        connection.execute(
            """
            UPDATE request_matches
            SET donor_response = ?
            WHERE id = ?
            """,
            (response_status, match_id)
        )

        connection.commit()

        return redirect(
            url_for(
                "request_results",
                request_id=match["request_id"]
            )
        )

    finally:
        connection.close()


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)

