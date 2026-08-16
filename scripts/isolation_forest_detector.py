from pathlib import Path
from datetime import datetime
import sqlite3

import pandas as pd
from sklearn.ensemble import IsolationForest

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "telecom_cell_health.db"

# The five KPI features the model is allowed to see.
# event_id is deliberately excluded: it is ground truth.
FEATURES = [
    "availability_pct",
    "throughput_mbps",
    "latency_ms",
    "call_drop_rate_pct",
    "active_users",
]

# Proportion of rows the model should treat as anomalous.
# 117 of 28,800 is roughly 0.4 percent.
CONTAMINATION = 0.004

RANDOM_STATE = 42

def load_measurements():
    connection = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT site_id, timestamp,
               availability_pct, throughput_mbps,
               latency_ms, call_drop_rate_pct, active_users
        FROM kpi_measurements
        """,
        connection
    )

    connection.close()

    return df

def describe(row, means, stds):
    """
    Work out which KPI is furthest from normal, and write a sentence.
    """
    worst_kpi = None
    worst_distance = -1

    for kpi in FEATURES:
        if stds[kpi] == 0:
            continue

        distance = abs(row[kpi] - means[kpi]) / stds[kpi]

        if distance > worst_distance:
            worst_distance = distance
            worst_kpi = kpi

    value = round(row[worst_kpi], 2)
    direction = "above" if row[worst_kpi] > means[worst_kpi] else "below"

    wording = {
        "availability_pct": "Availability",
        "throughput_mbps": "Throughput",
        "latency_ms": "Latency",
        "call_drop_rate_pct": "Call drop rate",
        "active_users": "Active users",
    }

    explanation = (
        f"{wording[worst_kpi]} of {value} is {direction} the normal pattern "
        f"for this network ({round(worst_distance, 1)} standard deviations "
        f"from the mean)."
    )

    return worst_kpi, round(worst_distance, 2), explanation

def run_detection():
    print("Isolation Forest anomaly detection")
    print("-" * 45)

    df = load_measurements()
    print(f"Measurements loaded:   {len(df)}")

    X = df[FEATURES]

    model = IsolationForest(
        n_estimators=100,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
    )

    model.fit(X)

    df["prediction"] = model.predict(X)
    df["score"] = model.score_samples(X)

    flagged = df[df["prediction"] == -1].copy()
    print(f"Anomalies detected:    {len(flagged)}")

    means = X.mean()
    stds = X.std()

    detected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    threshold = flagged["score"].quantile(0.5)
    rows = []

    for _, row in flagged.iterrows():
        main_kpi, distance, explanation = describe(row, means, stds)

        severity = "Critical" if row["score"] <= threshold else "Warning"

        rows.append((
            row["site_id"],
            row["timestamp"],
            "isolation_forest",
            severity,
            main_kpi,
            round(float(row["score"]), 4),
            explanation,
            detected_at,
        ))

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM detected_anomalies WHERE method = 'isolation_forest'"
    )

    cursor.executemany("""
        INSERT INTO detected_anomalies (
            site_id, timestamp, method, severity,
            main_kpi, anomaly_score, explanation, detected_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    connection.commit()
    connection.close()

    critical = sum(1 for r in rows if r[3] == "Critical")

    print(f"  Critical:            {critical}")
    print(f"  Warning:             {len(rows) - critical}")
    print("-" * 45)
    print("Detection complete.")


if __name__ == "__main__":
    run_detection()

