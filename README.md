
To verify the import:

```bash
python scripts/validate_database.py
```

---

## Running detection

Both detectors write to the `detected_anomalies` table. Each clears its
own previous results before running, so the other method is unaffected.

### Rule-based detection

```bash
python scripts/rule_detector.py
```

Applies the KPI thresholds from charter section 7.1. Produces 4,782
detections against 28,800 measurements.

### Isolation Forest detection

```bash
python scripts/isolation_forest_detector.py
```

Trains an unsupervised model on the five KPI features. Produces 116
detections.

### Evaluation

```bash
python scripts/evaluate_detections.py
```

Compares both methods against the 117 injected anomalies and reports
true positives, false positives, false negatives, precision and recall.

---

## Running the application

Two terminals are required.

### Terminal 1 — backend

```bash
python -m uvicorn backend.app.main:app --reload
```

Available at http://localhost:8000
Interactive API documentation at http://localhost:8000/docs

### Terminal 2 — frontend

```bash
cd frontend
npm run dev
```

Available at http://localhost:5173

---

## Running with Docker

```bash
docker compose up --build
```

Starts both services. The first build takes several minutes.

The `data` directory is mounted as a volume, so the SQLite database
persists across container restarts. The frontend waits for the backend
healthcheck to pass before starting.

To stop:

```bash
docker compose down
```

Note: the database must exist before starting the containers. Run the
import script first if `data/telecom_cell_health.db` is not present.

---

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | Confirm the backend and database are available |
| GET | /api/summary | Site and detection summary metrics |
| GET | /api/regions | Region reference data with site counts |
| GET | /api/sites | All sites |
| GET | /api/sites/{site_id} | Site metadata and latest KPI values |
| GET | /api/sites/{site_id}/measurements | Site KPI time series |
| GET | /api/anomalies | Detected anomalies with filters |
| POST | /api/detections/run | Run detection and store results |
| GET | /api/model/metrics | Evaluation metrics per method |

`/api/anomalies` accepts the following filters: `severity`, `region`,
`technology`, `date_from`, `date_to`, `method`, `site_id` and `limit`.

---

## Source data

| File | Rows | Contents |
|---|---|---|
| 01_regions.csv | 6 | Operating regions |
| 02_sites.csv | 60 | Cell site master data |
| 03_network_kpi_measurements.csv | 28,800 | Hourly KPI readings |
| 04_network_anomaly_events.csv | 117 | Ground-truth anomaly records |

The measurements cover 60 sites over 480 hourly readings each, from
2026-07-01 00:00:00 to 2026-07-20 23:00:00.

The `event_id` column in the measurements file is a ground-truth label.
It is excluded from every detection query, so neither the rule-based
detector nor the Isolation Forest has access to it. It is used only to
evaluate predictions.

---

## Results

| Metric | Rule-based | Isolation Forest |
|---|---|---|
| Measurements analysed | 28,800 | 28,800 |
| Anomalies detected | 4,782 | 116 |
| True positives | 94 | 10 |
| False positives | 4,688 | 106 |
| False negatives | 23 | 107 |
| Precision | 0.0197 | 0.0862 |
| Recall | 0.8034 | 0.0855 |

The rule-based method achieves high recall but very low precision. The
charter's availability warning threshold of 99.5% does not fit this
dataset, where normal availability ranges from 99.40% to 99.99%, so a
large proportion of healthy hours breach it. Critical detections (65)
are close to the number of injected critical events (60), indicating the
critical thresholds are appropriate.

The Isolation Forest produces a realistic detection volume but low
recall. It identifies statistical outliers, while many injected
anomalies are subtle enough to sit within the normal distribution.

Charter values were retained and the finding documented rather than
adjusted unilaterally.

---

## Known limitations

- The import script drops and recreates tables before inserting, so a
  failure partway through leaves a partial database. The database is
  fully reproducible from the immutable CSV files, so the risk is
  downtime rather than data loss.
- Value-level validation of timestamps, severity and technology is not
  implemented. Malformed values would be accepted.
- Invalid filter values on `/api/anomalies` return an empty result set
  rather than a 400 error.
- The dashboard has no method filter, so rule and Isolation Forest
  results appear together in the anomaly table.
- The site details page does not list detected anomaly periods.

---

## Project structure