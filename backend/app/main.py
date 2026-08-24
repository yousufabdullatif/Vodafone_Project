from pydantic import BaseModel
import subprocess
import sys
import time
from pathlib import Path

class DetectionRequest(BaseModel):
    method: str

from fastapi import FastAPI, HTTPException

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
    try:
        connection = get_db_connection()

        measurements = connection.execute(
            "SELECT COUNT(*) FROM kpi_measurements"
        ).fetchone()[0]

        connection.close()

        return {
            "status": "ok",
            "database": "connected",
            "measurements": measurements
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database not available. Run scripts/import_csv_to_sqlite.py first."
        )


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
    method: str | None = None,
    site_id: str | None = None,
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

    if method:
        query += " AND d.method = ?"
        params.append(method)

    if site_id:
        query += " AND d.site_id = ?"
        params.append(site_id)



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


@app.post("/api/detections/run")
def run_detections(request: DetectionRequest):
    allowed_methods = {"rule", "isolation_forest", "both"}

    if request.method not in allowed_methods:
        return {
            "error": "Invalid method. Use rule, isolation_forest, or both."
        }

    base_dir = Path(__file__).resolve().parent.parent.parent
    scripts_dir = base_dir / "scripts"

    start_time = time.time()

    methods_to_run = (
        ["rule", "isolation_forest"]
        if request.method == "both"
        else [request.method]
    )

    results = []

    for method in methods_to_run:
        if method == "rule":
            script_path = scripts_dir / "rule_detector.py"
        else:
            script_path = scripts_dir / "isolation_forest_detector.py"

        completed = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )

        if completed.returncode != 0:
            return {
                "method": method,
                "error": completed.stderr
            }

        results.append({
            "method": method,
            "output": completed.stdout
        })

    duration = round(time.time() - start_time, 3)

    connection = get_db_connection()

    total_rows = connection.execute(
        "SELECT COUNT(*) FROM kpi_measurements"
    ).fetchone()[0]

    detections_stored = connection.execute(
        """
        SELECT COUNT(*)
        FROM detected_anomalies
        WHERE method IN (?, ?)
        """,
        (
            "rule" if request.method in ("rule", "both") else "",
            "isolation_forest"
            if request.method in ("isolation_forest", "both")
            else ""
        )
    ).fetchone()[0]

    connection.close()

    return {
        "method": request.method,
        "rows_analysed": total_rows,
        "detections_stored": detections_stored,
        "duration_seconds": duration,
        "details": results
    }


@app.get("/api/model/metrics")
def get_model_metrics():
    connection = get_db_connection()

    truth = connection.execute("""
        SELECT site_id, timestamp
        FROM kpi_measurements
        WHERE event_id IS NOT NULL
    """).fetchall()

    truth_set = {(row["site_id"], row["timestamp"]) for row in truth}

    methods = connection.execute("""
        SELECT DISTINCT method FROM detected_anomalies ORDER BY method
    """).fetchall()

    results = []

    for method_row in methods:
        method = method_row["method"]

        detections = connection.execute("""
            SELECT site_id, timestamp
            FROM detected_anomalies
            WHERE method = ?
        """, (method,)).fetchall()

        predicted_set = {(row["site_id"], row["timestamp"]) for row in detections}

        true_positives = len(predicted_set & truth_set)
        false_positives = len(predicted_set - truth_set)
        false_negatives = len(truth_set - predicted_set)

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )

        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )

        results.append({
            "method": method,
            "true_anomalies": len(truth_set),
            "predicted": len(predicted_set),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": round(precision, 4),
            "recall": round(recall, 4)
        })

    connection.close()

    return results

@app.get("/api/sites/{site_id}")
def get_site(site_id: str):
    connection = get_db_connection()

    site = connection.execute("""
        SELECT
            s.site_id,
            s.site_name,
            s.technology,
            r.region_id,
            r.region_name
        FROM sites s
        JOIN regions r
            ON s.region_id = r.region_id
        WHERE s.site_id = ?
    """, (site_id,)).fetchone()

    if site is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail=f"Site not found: {site_id}"
        )

    latest = connection.execute("""
        SELECT
            timestamp,
            availability_pct,
            throughput_mbps,
            latency_ms,
            call_drop_rate_pct,
            active_users
        FROM kpi_measurements
        WHERE site_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (site_id,)).fetchone()

    detections = connection.execute("""
        SELECT COUNT(*) FROM detected_anomalies WHERE site_id = ?
    """, (site_id,)).fetchone()[0]

    connection.close()

    return {
        "site_id": site["site_id"],
        "site_name": site["site_name"],
        "region_id": site["region_id"],
        "region_name": site["region_name"],
        "technology": site["technology"],
        "detection_count": detections,
        "latest_kpis": {
            "timestamp": latest["timestamp"],
            "availability_pct": latest["availability_pct"],
            "throughput_mbps": latest["throughput_mbps"],
            "latency_ms": latest["latency_ms"],
            "call_drop_rate_pct": latest["call_drop_rate_pct"],
            "active_users": latest["active_users"]
        } if latest else None
    }

@app.get("/api/sites/{site_id}/measurements")
def get_site_measurements(
    site_id: str,
    date_from: str | None = None,
    date_to: str | None = None
):
    connection = get_db_connection()

    site = connection.execute(
        "SELECT site_id FROM sites WHERE site_id = ?", (site_id,)
    ).fetchone()

    if site is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail=f"Site not found: {site_id}"
        )

    query = """
        SELECT
            timestamp,
            availability_pct,
            throughput_mbps,
            latency_ms,
            call_drop_rate_pct,
            active_users
        FROM kpi_measurements
        WHERE site_id = ?
    """

    params = [site_id]

    if date_from:
        query += " AND timestamp >= ?"
        params.append(date_from)

    if date_to:
        query += " AND timestamp <= ?"
        params.append(date_to)

    query += " ORDER BY timestamp"

    rows = connection.execute(query, params).fetchall()

    connection.close()

    return [
        {
            "timestamp": row["timestamp"],
            "availability_pct": row["availability_pct"],
            "throughput_mbps": row["throughput_mbps"],
            "latency_ms": row["latency_ms"],
            "call_drop_rate_pct": row["call_drop_rate_pct"],
            "active_users": row["active_users"]
        }
        for row in rows
    ]