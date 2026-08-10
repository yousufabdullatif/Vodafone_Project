from pathlib import Path
from datetime import datetime
import sqlite3

# Where the database lives
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "telecom_cell_health.db"

# Thresholds from charter section 7.1
THRESHOLDS = {
    "availability_pct":   {"warning": 99.5, "critical": 98.0, "direction": "below"},
    "latency_ms":         {"warning": 80.0, "critical": 120.0, "direction": "above"},
    "call_drop_rate_pct": {"warning": 2.0,  "critical": 4.0,   "direction": "above"},
    "throughput_mbps":    {"warning": 15.0, "critical": 7.0,   "direction": "below"},
}

def check_measurement(row):
    """
    Look at one hour of readings and decide if anything is wrong.
    Returns None if everything is fine.
    """
    problems = []

    for kpi, limits in THRESHOLDS.items():
        value = row[kpi]

        if limits["direction"] == "below":
            if value < limits["critical"]:
                problems.append((kpi, value, "Critical"))
            elif value < limits["warning"]:
                problems.append((kpi, value, "Warning"))
        else:
            if value > limits["critical"]:
                problems.append((kpi, value, "Critical"))
            elif value > limits["warning"]:
                problems.append((kpi, value, "Warning"))

    if not problems:
        return None

    critical = [p for p in problems if p[2] == "Critical"]

    if critical:
        severity = "Critical"
        main_kpi, main_value, _ = critical[0]
    else:
        severity = "Warning"
        main_kpi, main_value, _ = problems[0]

    return {
        "severity": severity,
        "main_kpi": main_kpi,
        "main_value": main_value,
        "problem_count": len(problems),
    }

def build_explanation(result):
    """
    Turn the detection result into a sentence a human can read.
    """
    kpi = result["main_kpi"]
    value = result["main_value"]
    severity = result["severity"]

    wording = {
        "availability_pct":   f"Availability dropped to {value}%",
        "latency_ms":         f"Latency rose to {value} ms",
        "call_drop_rate_pct": f"Call drop rate rose to {value}%",
        "throughput_mbps":    f"Throughput fell to {value} Mbps",
    }

    sentence = wording[kpi]

    if severity == "Critical":
        sentence += ", which is well outside the acceptable range"
    else:
        sentence += ", which is outside the normal range"

    others = result["problem_count"] - 1

    if others == 1:
        sentence += ". One other KPI was also affected."
    elif others > 1:
        sentence += f". {others} other KPIs were also affected."
    else:
        sentence += "."

    return sentence

def run_detection():
    print("Rule-based anomaly detection")
    print("-" * 45)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Clear any previous rule results so re-running is safe
    cursor.execute("DELETE FROM detected_anomalies WHERE method = 'rule'")

    rows = cursor.execute("""
        SELECT site_id, timestamp,
               availability_pct, throughput_mbps,
               latency_ms, call_drop_rate_pct
        FROM kpi_measurements
    """).fetchall()

    print(f"Measurements analysed: {len(rows)}")

    detected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    detections = []

    for row in rows:
        result = check_measurement(row)

        if result is None:
            continue

        detections.append((
            row["site_id"],
            row["timestamp"],
            "rule",
            result["severity"],
            result["main_kpi"],
            None,
            build_explanation(result),
            detected_at,
        ))

    cursor.executemany("""
        INSERT INTO detected_anomalies (
            site_id, timestamp, method, severity,
            main_kpi, anomaly_score, explanation, detected_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, detections)

    connection.commit()
    connection.close()

    critical = sum(1 for d in detections if d[3] == "Critical")

    print(f"Anomalies detected:    {len(detections)}")
    print(f"  Critical:            {critical}")
    print(f"  Warning:             {len(detections) - critical}")
    print("-" * 45)
    print("Detection complete.")


if __name__ == "__main__":
    run_detection()