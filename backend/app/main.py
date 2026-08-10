from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from backend.app.database import get_db_connection


app = FastAPI(
    title="Telecom Cell Health API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/api/sites")
def get_sites():
    connection = get_db_connection()

    rows = connection.execute("""
        SELECT
            site_id,
            site_name,
            region_id,
            technology
        FROM sites
        ORDER BY site_id
    """).fetchall()

    connection.close()

    return [
        {
            "site_id": row["site_id"],
            "site_name": row["site_name"],
            "region_id": row["region_id"],
            "technology": row["technology"]
        }
        for row in rows
    ]


@app.get("/api/summary")
def get_summary():
    connection = get_db_connection()

    total_sites = connection.execute(
        "SELECT COUNT(*) FROM sites"
    ).fetchone()[0]

    total_anomalies = connection.execute(
        "SELECT COUNT(*) FROM anomaly_events"
    ).fetchone()[0]

    critical_anomalies = connection.execute(
        """
        SELECT COUNT(*)
        FROM anomaly_events
        WHERE LOWER(severity) = 'critical'
        """
    ).fetchone()[0]

    most_common_problem_row = connection.execute(
        """
        SELECT anomaly_type, COUNT(*) AS total
        FROM anomaly_events
        GROUP BY anomaly_type
        ORDER BY total DESC
        LIMIT 1
        """
    ).fetchone()

    latest_measurement_row = connection.execute(
        """
        SELECT MAX(timestamp)
        FROM kpi_measurements
        """
    ).fetchone()

    connection.close()

    return {
        "total_sites": total_sites,
        "total_anomalies": total_anomalies,
        "critical_anomalies": critical_anomalies,
        "most_common_problem": (
            most_common_problem_row["anomaly_type"]
            if most_common_problem_row
            else None
        ),
        "latest_measurement_time": latest_measurement_row[0]
    }


@app.get("/api/anomalies")
def get_anomalies(
    severity: str | None = None,
    region: str | None = None,
    technology: str | None = None
):
    connection = get_db_connection()

    query = """
        SELECT
            a.event_id,
            a.site_id,
            s.site_name,
            r.region_name,
            s.technology,
            a.timestamp,
            a.anomaly_type,
            a.severity
        FROM anomaly_events a
        JOIN sites s
            ON a.site_id = s.site_id
        JOIN regions r
            ON s.region_id = r.region_id
        WHERE 1 = 1
    """

    params = []

    if severity:
        query += " AND LOWER(a.severity) = LOWER(?)"
        params.append(severity)

    if region:
        query += " AND LOWER(r.region_name) = LOWER(?)"
        params.append(region)

    if technology:
        query += " AND LOWER(s.technology) = LOWER(?)"
        params.append(technology)

    query += " ORDER BY a.timestamp DESC"

    rows = connection.execute(query, params).fetchall()

    connection.close()

    return [
        {
            "event_id": row["event_id"],
            "site_id": row["site_id"],
            "site_name": row["site_name"],
            "region": row["region_name"],
            "technology": row["technology"],
            "timestamp": row["timestamp"],
            "anomaly_type": row["anomaly_type"],
            "severity": row["severity"]
        }
        for row in rows
    ]

    