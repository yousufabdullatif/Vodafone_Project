from pathlib import Path
import csv
import sqlite3


# Project folders
BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / "data" / "source"
DB_PATH = BASE_DIR / "data" / "telecom_cell_health.db"


EXPECTED_FILES = {
    "01_regions.csv": [
        "region_id",
        "region_name"
    ],

    "02_sites.csv": [
        "site_id",
        "site_name",
        "region_id",
        "technology"
    ],

    "03_network_kpi_measurements.csv": [
        "timestamp",
        "site_id",
        "event_id",
        "availability_pct",
        "throughput_mbps",
        "latency_ms",
        "call_drop_rate_pct",
        "active_users"
    ],

    "04_network_anomaly_events.csv": [
        "event_id",
        "site_id",
        "timestamp",
        "anomaly_type",
        "severity"
    ]
}


def validate_files():
    print("Checking source CSV files...\n")

    for filename, expected_headers in EXPECTED_FILES.items():

        file_path = SOURCE_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Missing required file: {filename}"
            )

        with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            actual_headers = next(reader)

        if actual_headers != expected_headers:
            raise ValueError(
                f"Invalid headers in {filename}\n"
                f"Expected: {expected_headers}\n"
                f"Found:    {actual_headers}"
            )

        print(f"[OK] {filename}")


def create_database():
    print("\nCreating SQLite database...")

    connection = sqlite3.connect(DB_PATH)

   
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS kpi_measurements;
    DROP TABLE IF EXISTS anomaly_events;
    DROP TABLE IF EXISTS sites;
    DROP TABLE IF EXISTS regions;

    CREATE TABLE regions (
        region_id TEXT PRIMARY KEY,
        region_name TEXT NOT NULL
    );

    CREATE TABLE sites (
        site_id TEXT PRIMARY KEY,
        site_name TEXT NOT NULL,
        region_id TEXT NOT NULL,
        technology TEXT NOT NULL,
        FOREIGN KEY (region_id)
            REFERENCES regions(region_id)
    );

    CREATE TABLE anomaly_events (
        event_id TEXT PRIMARY KEY,
        site_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        anomaly_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        FOREIGN KEY (site_id)
            REFERENCES sites(site_id)
    );

    CREATE TABLE kpi_measurements (
        timestamp TEXT NOT NULL,
        site_id TEXT NOT NULL,
        event_id TEXT,
        availability_pct REAL NOT NULL,
        throughput_mbps REAL NOT NULL,
        latency_ms REAL NOT NULL,
        call_drop_rate_pct REAL NOT NULL,
        active_users INTEGER NOT NULL,

        FOREIGN KEY (site_id)
            REFERENCES sites(site_id),

        FOREIGN KEY (event_id)
            REFERENCES anomaly_events(event_id),

        UNIQUE (site_id, timestamp)
    );
    """)

    connection.commit()
    connection.close()

    print(f"[OK] Database created: {DB_PATH}")

def import_regions():
    print("\nImporting regions...")

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.cursor()

    file_path = SOURCE_DIR / "01_regions.csv"

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)

        for row in reader:

            cursor.execute(
                """
                INSERT INTO regions (
                    region_id,
                    region_name
                )
                VALUES (?, ?)
                """,
                (
                    row["region_id"],
                    row["region_name"]
                )
            )

    connection.commit()
    connection.close()

    print("[OK] Regions imported.")

def import_sites():
    print("\nImporting sites...")

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    cursor = connection.cursor()

    file_path = SOURCE_DIR / "02_sites.csv"

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cursor.execute(
                """
                INSERT INTO sites (
                    site_id,
                    site_name,
                    region_id,
                    technology
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    row["site_id"],
                    row["site_name"],
                    row["region_id"],
                    row["technology"]
                )
            )

    connection.commit()
    connection.close()

    print("[OK] Sites imported.")

def import_anomaly_events():
    print("\nImporting anomaly events...")

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    cursor = connection.cursor()

    file_path = SOURCE_DIR / "04_network_anomaly_events.csv"

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cursor.execute(
                """
                INSERT INTO anomaly_events (
                    event_id,
                    site_id,
                    timestamp,
                    anomaly_type,
                    severity
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    row["event_id"],
                    row["site_id"],
                    row["timestamp"],
                    row["anomaly_type"],
                    row["severity"]
                )
            )

    connection.commit()
    connection.close()

    print("[OK] Anomaly events imported.")


def import_kpi_measurements():
    print("\nImporting KPI measurements...")

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    cursor = connection.cursor()

    file_path = SOURCE_DIR / "03_network_kpi_measurements.csv"

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cursor.execute(
                """
                INSERT INTO kpi_measurements (
                    timestamp,
                    site_id,
                    event_id,
                    availability_pct,
                    throughput_mbps,
                    latency_ms,
                    call_drop_rate_pct,
                    active_users
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["timestamp"],
                    row["site_id"],
                    row["event_id"] if row["event_id"] else None,
                    float(row["availability_pct"]),
                    float(row["throughput_mbps"]),
                    float(row["latency_ms"]),
                    float(row["call_drop_rate_pct"]),
                    int(row["active_users"])
                )
            )

    connection.commit()
    connection.close()

    print("[OK] KPI measurements imported.")


if __name__ == "__main__":
    validate_files()
    create_database()

    import_regions()
    import_sites()
    import_anomaly_events()
    import_kpi_measurements()

    print("\nImport completed successfully.")
