# Telecom Cell Health Monitor
## Source Data Dictionary

---

## 1. 01_regions.csv

| Column | Type | Description | Key |
|---|---|---|---|
| region_id | Integer | Unique identifier for the region | Primary Key |
| region_name | Text | Name of the region | - |

---

## 2. 02_sites.csv

| Column | Type | Description | Key |
|---|---|---|---|
| site_id | Text | Unique identifier for the site | Primary Key |
| site_name | Text | Name of the site | - |
| region_id | Integer | Identifier of the region containing the site | Foreign Key |
| technology | Text | Network technology used by the site | - |

---

## 3. 03_network_kpi_measurements.csv

| Column | Type | Description | Key |
|---|---|---|---|
| timestamp | Text | Date and time of the KPI measurement | - |
| site_id | Text | Identifier of the site being measured | Foreign Key |
| event_id | Integer | Identifier of the related anomaly event, if available | Foreign Key |
| availability_pct | Real | Network availability percentage | - |
| throughput_mbps | Real | Network throughput in Mbps | - |
| latency_ms | Real | Network latency in milliseconds | - |
| call_drop_rate_pct | Real | Call drop rate percentage | - |
| active_users | Integer | Number of active users at the measurement time | - |

---

## 4. 04_network_anomaly_events.csv

| Column | Type | Description | Key |
|---|---|---|---|
| event_id | Integer | Unique identifier for the anomaly event | Primary Key |
| site_id | Text | Identifier of the affected site | Foreign Key |
| timestamp | Text | Date and time when the anomaly event occurred | - |
| anomaly_type | Text | Type of detected anomaly | - |
| severity | Text | Severity level of the anomaly | - |sss