# CSV to SQLite Database Mapping

---

## CSV Files → SQLite Tables

| CSV File | SQLite Table |
|---|---|
| 01_regions.csv | regions |
| 02_sites.csv | sites |
| 03_network_kpi_measurements.csv | kpi_measurements |
| 04_network_anomaly_events.csv | anomaly_events |

---

# 1. regions

Source:

01_regions.csv

Columns:

- region_id
- region_name

Primary Key:

region_id

---

# 2. sites

Source:

02_sites.csv

Columns:

- site_id
- site_name
- region_id
- technology

Primary Key:

site_id

Foreign Key:

region_id → regions.region_id

---

# 3. kpi_measurements

Source:

03_network_kpi_measurements.csv

Columns:

- timestamp
- site_id
- event_id
- availability_pct
- throughput_mbps
- latency_ms
- call_drop_rate_pct
- active_users

Primary Key:

To be assigned during SQLite implementation.

Foreign Keys:

site_id → sites.site_id

event_id → anomaly_events.event_id

---

# 4. anomaly_events

Source:

04_network_anomaly_events.csv

Columns:

- event_id
- site_id
- timestamp
- anomaly_type
- severity

Primary Key:

event_id

Foreign Key:

site_id → sites.site_id