# CSV Relationships

---

## 1. regions → sites

One region can contain many sites.

Relationship:

regions.region_id
        ↓
sites.region_id

Cardinality:

1 Region → Many Sites

---

## 2. sites → kpi_measurements

One site can have many KPI measurements.

Relationship:

sites.site_id
        ↓
kpi_measurements.site_id

Cardinality:

1 Site → Many KPI Measurements

---

## 3. sites → anomaly_events

One site can have many anomaly events.

Relationship:

sites.site_id
        ↓
anomaly_events.site_id

Cardinality:

1 Site → Many Anomaly Events

---

## 4. anomaly_events → kpi_measurements

An anomaly event can be associated with KPI measurements.

Relationship:

anomaly_events.event_id
        ↓
kpi_measurements.event_id

Cardinality:

1 Anomaly Event → Many KPI Measurements

---

## Overall Relationship

regions
   │
   │ 1
   │
   │ *
   ▼
sites
   │
   ├───────────────┐
   │               │
   │ *             │ *
   ▼               ▼
kpi_measurements  anomaly_events