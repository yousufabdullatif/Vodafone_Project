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
        "SELECT COUNT(*) FROM detected_anomalies"
    ).fetchone()[0]

    critical_anomalies = connection.execute(
        """
        SELECT COUNT(*)
        FROM detected_anomalies
        WHERE severity = 'Critical'
        """
    ).fetchone()[0]

    most_common_problem_row = connection.execute(
        """
        SELECT main_kpi, COUNT(*) AS total
        FROM detected_anomalies
        GROUP BY main_kpi
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
            most_common_problem_row["main_kpi"]
            if most_common_problem_row
            else None
        ),
        "latest_measurement_time": latest_measurement_row[0]
    }


@app.get("/api/anomalies")
def get_anomalies(
    severity: str | None = None,
    region: str | None = None,
    technology: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 200
):
    connection = get_db_connection()

    query = """
        SELECT
            d.detection_id,
            d.site_id,
            s.site_name,
            r.region_name,
            s.technology,
            d.timestamp,
            d.method,
            d.severity,
            d.main_kpi,
            d.anomaly_score,
            d.explanation
        FROM detected_anomalies d
        JOIN sites s
            ON d.site_id = s.site_id
        JOIN regions r
            ON s.region_id = r.region_id
        WHERE 1 = 1
    """

    params = []

    if severity:
        query += " AND d.severity = ?"
        params.append(severity)

    if region:
        query += " AND r.region_name = ?"
        params.append(region)

    if technology:
        query += " AND s.technology = ?"
        params.append(technology)

    if date_from:
        query += " AND d.timestamp >= ?"
        params.append(date_from)

    if date_to:
        query += " AND d.timestamp <= ?"
        params.append(date_to)

    query += " ORDER BY d.timestamp DESC LIMIT ?"
    params.append(limit)

    rows = connection.execute(query, params).fetchall()

    connection.close()

    return [
        {
            "detection_id": row["detection_id"],
            "site_id": row["site_id"],
            "site_name": row["site_name"],
            "region": row["region_name"],
            "technology": row["technology"],
            "timestamp": row["timestamp"],
            "method": row["method"],
            "severity": row["severity"],
            "main_kpi": row["main_kpi"],
            "anomaly_score": row["anomaly_score"],
            "explanation": row["explanation"]
        }
        for row in rows
    ]

@app.get("/api/regions")
def get_regions():
    connection = get_db_connection()

    rows = connection.execute("""
        SELECT
            r.region_id,
            r.region_name,
            COUNT(s.site_id) AS site_count
        FROM regions r
        LEFT JOIN sites s
            ON s.region_id = r.region_id
        GROUP BY r.region_id, r.region_name
        ORDER BY r.region_id
    """).fetchall()

    connection.close()

    return [
        {
            "region_id": row["region_id"],
            "region_name": row["region_name"],
            "site_count": row["site_count"]
        }
        for row in rows
    ]