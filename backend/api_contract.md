# API Contract

Base URL:

/api


## GET /api/health

Purpose:
Check whether the backend and SQLite database are available.

Response:

{
  "status": "ok"
}


## GET /api/summary

Purpose:
Return dashboard summary metrics.

Response:

{
  "sites": 0,
  "anomalies": 0,
  "critical": 0,
  "warning": 0
}


## GET /api/regions

Purpose:
Return all regions.


## GET /api/sites

Purpose:
Return all network sites.

Optional filters:

region_id
technology


## GET /api/sites/{site_id}

Purpose:
Return details for one site.


## GET /api/sites/{site_id}/measurements

Purpose:
Return KPI measurements for a site.


## GET /api/anomalies

Purpose:
Return detected anomalies.

Optional filters:

region_id
technology
severity
date


## POST /api/detections/run

Purpose:
Run anomaly detection.


## GET /api/model/metrics

Purpose:
Return model evaluation metrics.