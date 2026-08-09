from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "telecom_cell_health.db"


connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


tables = [
    "regions",
    "sites",
    "anomaly_events",
    "kpi_measurements"
]


print("Database Validation\n")


for table in tables:

    cursor.execute(f"SELECT COUNT(*) FROM {table}")

    count = cursor.fetchone()[0]

    print(f"{table}: {count} rows")

print("\nChecking foreign key relationships...")

cursor.execute("PRAGMA foreign_key_check")
foreign_key_errors = cursor.fetchall()

if len(foreign_key_errors) == 0:
    print("[OK] No foreign key errors.")
else:
    print("[ERROR] Foreign key problems found:")
    for error in foreign_key_errors:
        print(error)


print("\nChecking duplicate KPI measurements...")

cursor.execute("""
    SELECT site_id, timestamp, COUNT(*)
    FROM kpi_measurements
    GROUP BY site_id, timestamp
    HAVING COUNT(*) > 1
""")

duplicates = cursor.fetchall()

if len(duplicates) == 0:
    print("[OK] No duplicate site/timestamp measurements.")
else:
    print("[ERROR] Duplicate measurements found:")
    for row in duplicates:
        print(row)


connection.close()
