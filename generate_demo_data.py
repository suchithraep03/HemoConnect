import random
from datetime import date, timedelta

from database import get_connection, initialize_database


# Reproducible fictional data for a college demonstration.
random.seed(42)

initialize_database()

BLOOD_GROUPS = [
    "A+", "A-", "B+", "B-",
    "AB+", "AB-", "O+", "O-"
]

DEPARTMENTS = [
    "Electronics and Communication Engineering",
    "Computer Science and Engineering",
    "Electrical and Electronics Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
]

ACADEMIC_YEARS = [
    "First Year",
    "Second Year",
    "Third Year",
    "Fourth Year",
]

PALAKKAD_DEMO_LOCATIONS = [
    "Palakkad Town - DEMO",
    "Akathethara - DEMO",
    "Olavakkode - DEMO",
    "Chandranagar - DEMO",
    "Mannarkkad - DEMO",
    "Kanjikode - DEMO",
    "Pattambi - DEMO",
    "Shoranur - DEMO",
]

connection = get_connection()
inserted = 0

try:
    for number in range(1, 101):

        student_id = f"DEMO{number:04d}"
        email = f"student{number:03d}@example.com"

        # Skip records that already exist.
        existing = connection.execute(
            "SELECT id FROM donors WHERE email = ?",
            (email,)
        ).fetchone()

        if existing:
            continue

        blood_group = random.choice(BLOOD_GROUPS)
        department = random.choice(DEPARTMENTS)
        academic_year = random.choice(ACADEMIC_YEARS)
        location = random.choice(PALAKKAD_DEMO_LOCATIONS)

        # Fictional donation dates for testing the interface.
        if random.random() < 0.65:
            days_ago = random.randint(120, 900)
            last_donation_date = (
                date.today() - timedelta(days=days_ago)
            ).isoformat()
        else:
            last_donation_date = None

        # These are deliberately non-contactable placeholders.
        phone = f"000000{number:04d}"

        # Random availability for the demonstration.
        available = random.choice([0, 1])

        connection.execute("""
            INSERT INTO donors (
                student_id,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            f"Demo Student {number:03d}",
            email,
            phone,
            blood_group,
            department,
            academic_year,
            last_donation_date,
            location,
            available,
            1
        ))

        inserted += 1

    connection.commit()

finally:
    connection.close()


print(f"Demo dataset ready. Added {inserted} fictional donors.")
print("All sample locations and donation dates are fictional.")
print("Do not use the placeholder phone numbers for contact.")