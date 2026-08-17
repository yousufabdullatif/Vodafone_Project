import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";


type Summary = {
  total_sites: number;
  total_anomalies: number;
  critical_anomalies: number;
  most_common_problem: string | null;
  latest_measurement_time: string | null;
};


type Region = {
  region_id: string;
  region_name: string;
  site_count?: number;
};


type Anomaly = {
  detection_id?: number;
  event_id?: string;
  site_id: string;
  site_name?: string;
  region?: string;
  region_name?: string;
  technology?: string;
  timestamp?: string;
  detected_time?: string;
  main_kpi?: string;
  anomaly_type?: string;
  severity: string;
  explanation?: string;
};


type SiteDetails = {
  site_id: string;
  site_name: string;
  region?: string;
  region_name?: string;
  technology: string;

  availability_pct?: number;
  throughput_mbps?: number;
  latency_ms?: number;
  call_drop_rate_pct?: number;
  active_users?: number;
};


type Measurement = {
  timestamp: string;
  availability_pct: number;
  throughput_mbps: number;
  latency_ms: number;
  call_drop_rate_pct: number;
  active_users: number;
};


function App() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);

  const [region, setRegion] = useState("");
  const [technology, setTechnology] = useState("");
  const [severity, setSeverity] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(
    null
  );

  const [siteDetails, setSiteDetails] =
    useState<SiteDetails | null>(null);

  const [measurements, setMeasurements] =
    useState<Measurement[]>([]);

  const [siteLoading, setSiteLoading] = useState(false);
  const [siteError, setSiteError] = useState("");

  const [dashboardLoading, setDashboardLoading] =
    useState(true);

  const [dashboardError, setDashboardError] =
    useState("");


  // ---------------------------------------------------------
  // DASHBOARD DATA
  // ---------------------------------------------------------

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/summary`).then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load summary");
        }

        return response.json();
      }),

      fetch(`${API_BASE_URL}/api/regions`).then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load regions");
        }

        return response.json();
      }),
    ])
      .then(([summaryData, regionsData]) => {
        setSummary(summaryData);
        setRegions(regionsData);
      })
      .catch((error) => {
        setDashboardError(error.message);
      })
      .finally(() => {
        setDashboardLoading(false);
      });
  }, []);


  useEffect(() => {
    const params = new URLSearchParams();

    if (region) {
      params.append("region", region);
    }

    if (technology) {
      params.append("technology", technology);
    }

    if (severity) {
      params.append("severity", severity);
    }

    if (dateFrom) {
      params.append("date_from", dateFrom);
    }

    if (dateTo) {
      params.append("date_to", dateTo);
    }

    params.append("limit", "5000");

    const url =
      `${API_BASE_URL}/api/anomalies?${params.toString()}`;

    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load anomalies");
        }

        return response.json();
      })
      .then((data) => {
        setAnomalies(data);
      })
      .catch((error) => {
        setDashboardError(error.message);
      });
  }, [
    region,
    technology,
    severity,
    dateFrom,
    dateTo,
  ]);


  // ---------------------------------------------------------
  // SITE DETAILS DATA
  // ---------------------------------------------------------

  useEffect(() => {
    if (!selectedSiteId) {
      return;
    }

    setSiteLoading(true);
    setSiteError("");
    setSiteDetails(null);
    setMeasurements([]);

    Promise.all([
      fetch(
        `${API_BASE_URL}/api/sites/${selectedSiteId}`
      ).then((response) => {
        if (response.status === 404) {
          throw new Error("Site not found");
        }

        if (!response.ok) {
          throw new Error("Failed to load site details");
        }

        return response.json();
      }),

      fetch(
        `${API_BASE_URL}/api/sites/${selectedSiteId}/measurements`
      ).then((response) => {
        if (!response.ok) {
          throw new Error(
            "Failed to load site measurements"
          );
        }

        return response.json();
      }),
    ])
      .then(([siteData, measurementData]) => {
        setSiteDetails(siteData);
        setMeasurements(measurementData);
      })
      .catch((error) => {
        setSiteError(error.message);
      })
      .finally(() => {
        setSiteLoading(false);
      });
  }, [selectedSiteId]);


  // ---------------------------------------------------------
  // ANOMALIES FOR SELECTED SITE
  // ---------------------------------------------------------

  const selectedSiteAnomalies = useMemo(() => {
    if (!selectedSiteId) {
      return [];
    }

    return anomalies.filter(
      (anomaly) => anomaly.site_id === selectedSiteId
    );
  }, [anomalies, selectedSiteId]);


  // ---------------------------------------------------------
  // SITE DETAILS PAGE
  // ---------------------------------------------------------

  if (selectedSiteId) {
    if (siteLoading) {
      return (
        <div className="message">
          Loading site details...
        </div>
      );
    }

    if (siteError) {
      return (
        <div className="site-details">
          <button
            className="back-button"
            onClick={() => setSelectedSiteId(null)}
          >
            ← Back to Dashboard
          </button>

          <div className="error-message">
            Error: {siteError}
          </div>
        </div>
      );
    }

    if (!siteDetails) {
      return (
        <div className="message">
          No site information available.
        </div>
      );
    }

    const siteRegion =
      siteDetails.region ??
      siteDetails.region_name ??
      "Unknown";

    return (
      <div className="site-details">
        <button
          className="back-button"
          onClick={() => setSelectedSiteId(null)}
        >
          ← Back to Dashboard
        </button>

        <div className="site-header">
          <div>
            <h1>{siteDetails.site_name}</h1>

            <p className="site-id">
              {siteDetails.site_id}
            </p>
          </div>

          <div className="site-meta">
            <div>
              <span>Region</span>
              <strong>{siteRegion}</strong>
            </div>

            <div>
              <span>Technology</span>
              <strong>
                {siteDetails.technology}
              </strong>
            </div>
          </div>
        </div>


        <section className="details-section">
          <h2>KPI Trends</h2>

          <p className="section-description">
            {measurements.length} hourly measurements
          </p>


          <div className="charts-grid">

            <div className="chart-card">
              <h3>Availability (%)</h3>

              <div className="chart-container">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart data={measurements}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="timestamp"
                      minTickGap={50}
                    />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="availability_pct"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>


            <div className="chart-card">
              <h3>Throughput (Mbps)</h3>

              <div className="chart-container">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart data={measurements}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="timestamp"
                      minTickGap={50}
                    />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="throughput_mbps"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>


            <div className="chart-card">
              <h3>Latency (ms)</h3>

              <div className="chart-container">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart data={measurements}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="timestamp"
                      minTickGap={50}
                    />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="latency_ms"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>


            <div className="chart-card">
              <h3>Call Drop Rate (%)</h3>

              <div className="chart-container">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart data={measurements}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="timestamp"
                      minTickGap={50}
                    />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="call_drop_rate_pct"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>


            <div className="chart-card">
              <h3>Active Users</h3>

              <div className="chart-container">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart data={measurements}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="timestamp"
                      minTickGap={50}
                    />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="active_users"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        </section>


        <section className="details-section">
          <h2>Detected Anomalies</h2>

          {selectedSiteAnomalies.length === 0 ? (
            <p>
              No detected anomalies available for this site.
            </p>
          ) : (
            <div className="table-wrapper">
              <table className="anomaly-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Severity</th>
                    <th>Main KPI</th>
                    <th>Explanation</th>
                  </tr>
                </thead>

                <tbody>
                  {selectedSiteAnomalies.map(
                    (anomaly, index) => (
                      <tr
                        key={
                          anomaly.detection_id ??
                          anomaly.event_id ??
                          index
                        }
                      >
                        <td>
                          {anomaly.detected_time ??
                            anomaly.timestamp ??
                            "-"}
                        </td>

                        <td>
                          {anomaly.severity}
                        </td>

                        <td>
                          {anomaly.main_kpi ??
                            anomaly.anomaly_type ??
                            "-"}
                        </td>

                        <td>
                          {anomaly.explanation ??
                            "-"}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    );
  }


  // ---------------------------------------------------------
  // DASHBOARD
  // ---------------------------------------------------------

  if (dashboardLoading) {
    return (
      <div className="message">
        Loading dashboard...
      </div>
    );
  }

  if (dashboardError) {
    return (
      <div className="message">
        Error: {dashboardError}
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="message">
        No dashboard data available.
      </div>
    );
  }


  return (
    <div className="dashboard">
      <h1>Telecom Cell Health Monitor</h1>

      <p className="subtitle">
        Network Operations Dashboard
      </p>


      <div className="cards">
        <div className="card">
          <h2>Total Sites</h2>
          <p>{summary.total_sites}</p>
        </div>

        <div className="card">
          <h2>Anomalies</h2>
          <p>{summary.total_anomalies}</p>
        </div>

        <div className="card">
          <h2>Critical</h2>
          <p>{summary.critical_anomalies}</p>
        </div>

        <div className="card">
          <h2>Most Common Problem</h2>

          <p>
            {summary.most_common_problem ?? "None"}
          </p>
        </div>
      </div>


      <div className="latest">
        Latest measurement:{" "}
        {summary.latest_measurement_time ?? "Unknown"}
      </div>


      <section className="anomaly-section">
        <div className="section-title-row">
          <h2>Detected Anomalies</h2>
        </div>


        <div className="filters">

          <label>
            Region

            <select
              value={region}
              onChange={(event) =>
                setRegion(event.target.value)
              }
            >
              <option value="">
                All Regions
              </option>

              {regions.map((item) => (
                <option
                  key={item.region_id}
                  value={item.region_name}
                >
                  {item.region_name}
                </option>
              ))}
            </select>
          </label>


          <label>
            Technology

            <select
              value={technology}
              onChange={(event) =>
                setTechnology(event.target.value)
              }
            >
              <option value="">
                All Technologies
              </option>

              <option value="4G">4G</option>
              <option value="5G">5G</option>
            </select>
          </label>


          <label>
            Severity

            <select
              value={severity}
              onChange={(event) =>
                setSeverity(event.target.value)
              }
            >
              <option value="">
                All Severities
              </option>

              <option value="Critical">
                Critical
              </option>

              <option value="Warning">
                Warning
              </option>
            </select>
          </label>


          <label>
            From

            <input
              type="date"
              value={dateFrom}
              onChange={(event) =>
                setDateFrom(event.target.value)
              }
            />
          </label>


          <label>
            To

            <input
              type="date"
              value={dateTo}
              onChange={(event) =>
                setDateTo(event.target.value)
              }
            />
          </label>

        </div>


        <div className="table-wrapper">
          <table className="anomaly-table">
            <thead>
              <tr>
                <th>Site</th>
                <th>Region</th>
                <th>Technology</th>
                <th>Detected Time</th>
                <th>Main KPI</th>
                <th>Severity</th>
                <th>Explanation</th>
              </tr>
            </thead>

            <tbody>
              {anomalies.map((anomaly, index) => (
                <tr
                  key={
                    anomaly.detection_id ??
                    anomaly.event_id ??
                    index
                  }
                  className="clickable-row"
                  onClick={() =>
                    setSelectedSiteId(
                      anomaly.site_id
                    )
                  }
                >
                  <td>
                    {anomaly.site_id}

                    {anomaly.site_name && (
                      <div>
                        {anomaly.site_name}
                      </div>
                    )}
                  </td>

                  <td>
                    {anomaly.region ??
                      anomaly.region_name ??
                      "-"}
                  </td>

                  <td>
                    {anomaly.technology ?? "-"}
                  </td>

                  <td>
                    {anomaly.detected_time ??
                      anomaly.timestamp ??
                      "-"}
                  </td>

                  <td>
                    {anomaly.main_kpi ??
                      anomaly.anomaly_type ??
                      "-"}
                  </td>

                  <td>
                    {anomaly.severity}
                  </td>

                  <td>
                    {anomaly.explanation ?? "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}


export default App;


