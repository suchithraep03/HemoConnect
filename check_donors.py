import sqlite3

conn = sqlite3.connect("hemoconnect.db")
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM donors")
print("Total donors:", cursor.fetchone()[0])

cursor.execute("""
    SELECT id, full_name, blood_group, available, consent
    FROM donors
""")

donors = cursor.fetchall()

print("\nDonor Details:")

for donor in donors:
    print(
        f"ID: {donor['id']}, "
        f"Name: {donor['full_name']}, "
        f"Blood Group: {donor['blood_group']}, "
        f"Available: {donor['available']}, "
        f"Consent: {donor['consent']}"
    )

conn.close()