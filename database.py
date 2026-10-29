import sqlite3

DATABASE_NAME = "hemoconnect.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS donors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                department TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                last_donation_date TEXT,
                location TEXT NOT NULL DEFAULT 'Palakkad',
                available INTEGER NOT NULL DEFAULT 1,
                consent INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS blood_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_name TEXT NOT NULL,
                requester_email TEXT NOT NULL,
                requester_phone TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                component TEXT NOT NULL,
                units INTEGER NOT NULL,
                hospital_name TEXT NOT NULL,
                hospital_address TEXT NOT NULL,
                urgency TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                requester_donor_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS request_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                donor_id INTEGER NOT NULL,
                donor_response TEXT NOT NULL DEFAULT 'Awaiting Response',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(request_id, donor_id),
                FOREIGN KEY(request_id)
                    REFERENCES blood_requests(id),
                FOREIGN KEY(donor_id)
                    REFERENCES donors(id)
            )
        """)

        # Add missing columns to older databases without deleting records.
        donor_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(donors)"
            ).fetchall()
        }

        donor_additions = {
            "student_id": "TEXT",
            "location": "TEXT NOT NULL DEFAULT 'Palakkad'",
            "available": "INTEGER NOT NULL DEFAULT 1",
            "consent": "INTEGER NOT NULL DEFAULT 0",
        }

        for column, definition in donor_additions.items():
            if column not in donor_columns:
                connection.execute(
                    f"ALTER TABLE donors ADD COLUMN {column} {definition}"
                )

        request_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(blood_requests)"
            ).fetchall()
        }

        request_additions = {
            "urgency": "TEXT NOT NULL DEFAULT 'Normal'",
            "status": "TEXT NOT NULL DEFAULT 'Pending'",
            "requester_donor_id": "INTEGER",
        }

        for column, definition in request_additions.items():
            if column not in request_columns:
                connection.execute(
                    f"ALTER TABLE blood_requests ADD COLUMN "
                    f"{column} {definition}"
                )

        match_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(request_matches)"
            ).fetchall()
        }

        if "donor_response" not in match_columns:
            connection.execute("""
                ALTER TABLE request_matches
                ADD COLUMN donor_response TEXT
                NOT NULL DEFAULT 'Awaiting Response'
            """)

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print("HemoConnect database initialized successfully!")