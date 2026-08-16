from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "telecom_cell_health.db"


def get_ground_truth(connection):
    rows = connection.execute(
        """
        SELECT site_id, timestamp
        FROM kpi_measurements
        WHERE event_id IS NOT NULL
        """
    ).fetchall()

    return {
        (row["site_id"], row["timestamp"])
        for row in rows
    }


def get_predictions(connection, method):
    rows = connection.execute(
        """
        SELECT site_id, timestamp
        FROM detected_anomalies
        WHERE method = ?
        """,
        (method,)
    ).fetchall()

    return {
        (row["site_id"], row["timestamp"])
        for row in rows
    }


def evaluate_method(connection, method, ground_truth):
    predictions = get_predictions(connection, method)

    true_positives = len(predictions & ground_truth)
    false_positives = len(predictions - ground_truth)
    false_negatives = len(ground_truth - predictions)

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

    return {
        "method": method,
        "true_injected_anomalies": len(ground_truth),
        "predicted_anomalies": len(predictions),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
    }


def print_results(results):
    print("\n" + "=" * 50)
    print(f"Detection Method: {results['method']}")
    print("=" * 50)

    print(f"True injected anomalies : {results['true_injected_anomalies']}")
    print(f"Predicted anomalies     : {results['predicted_anomalies']}")
    print(f"True positives          : {results['true_positives']}")
    print(f"False positives         : {results['false_positives']}")
    print(f"False negatives         : {results['false_negatives']}")
    print(f"Precision               : {results['precision']:.4f}")
    print(f"Recall                  : {results['recall']:.4f}")


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    ground_truth = get_ground_truth(connection)

    print("Telecom Cell Health - Detection Evaluation")
    print(f"\nGround-truth anomaly measurements: {len(ground_truth)}")

    for method in ["rule", "isolation_forest"]:
        results = evaluate_method(
            connection,
            method,
            ground_truth
        )

        print_results(results)

    connection.close()


if __name__ == "__main__":
    main()