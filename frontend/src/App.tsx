import { useEffect, useState } from "react";
import "./App.css";

type Summary = {
  total_sites: number;
  total_anomalies: number;
  critical_anomalies: number;
  most_common_problem: string | null;
  latest_measurement_time: string | null;
};

type Anomaly = {
  detection_id: number;
  site_id: string;
  site_name: string;
  region: string;
  technology: string;
  timestamp: string;
  method: string;
  severity: string;
  main_kpi: string;
  anomaly_score: number | null;
  explanation: string;
};

type Region = {
  region_id: string;
  region_name: string;
  site_count: number;
};

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [regionList, setRegionList] = useState<Region[]>([]);

  const [region, setRegion] = useState("");
  const [technology, setTechnology] = useState("");
  const [severity, setSeverity] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/summary`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load summary");
        }

        return response.json();
      })
      .then((data) => {
        setSummary(data);
      })
      .catch((err) => {
        setError(err.message);
      });
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/api/regions`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load regions");
        }

        return response.json();
      })
      .then((data) => {
        setRegionList(data);
      })
      .catch((err) => {
        setError(err.message);
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
      params.append("date_from", dateFrom + " 00:00:00");
    }

    if (dateTo) {
      params.append("date_to", dateTo + " 23:59:59");
    }

    const queryString = params.toString();

    const url = queryString
      ? `${API_BASE}/api/anomalies?${queryString}`
      : `${API_BASE}/api/anomalies`;

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
      .catch((err) => {
        setError(err.message);
      });
  }, [region, technology, severity, dateFrom, dateTo]);

  if (error) {
    return <div className="message">Error: {error}</div>;
  }

  if (!summary) {
    return <div className="message">Loading dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Telecom Cell Health Monitor</h1>
      <p className="subtitle">Network Operations Dashboard</p>

      <div className="cards">
        <div className="card">
          <h2>Total Sites</h2>
          <p>{summary.total_sites}</p>
        </div>

        <div className="card">
          <h2>Detected Anomalies</h2>
          <p>{summary.total_anomalies}</p>
        </div>

        <div className="card">
          <h2>Critical</h2>
          <p>{summary.critical_anomalies}</p>
        </div>

        <div className="card">
          <h2>Most Common Problem</h2>
          <p>{summary.most_common_problem ?? "None"}</p>
        </div>
      </div>

      <div className="latest">
        Latest measurement: {summary.latest_measurement_time ?? "Unknown"}
      </div>

      <section className="anomaly-section">
        <div className="section-header">
          <h2>Detected Anomalies</h2>
          <span>
            Showing {Math.min(anomalies.length, 20)} of {anomalies.length} records
          </span>
        </div>

        <div className="filters">
          <label>
            Region
            <select
              value={region}
              onChange={(event) => setRegion(event.target.value)}
            >
              <option value="">All</option>

              {regionList.map((item) => (
                <option key={item.region_id} value={item.region_name}>
                  {item.region_name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Technology
            <select
              value={technology}
              onChange={(event) => setTechnology(event.target.value)}
            >
              <option value="">All</option>
              <option value="2G">2G</option>
              <option value="4G">4G</option>
              <option value="5G">5G</option>
            </select>
          </label>

          <label>
            Severity
            <select
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
            >
              <option value="">All</option>
              <option value="Critical">Critical</option>
              <option value="Warning">Warning</option>
            </select>
          </label>

          <label>
            From
            <input
              type="date"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
            />
          </label>

          <label>
            To
            <input
              type="date"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
            />
          </label>

          <button
            className="reset-button"
            onClick={() => {
              setRegion("");
              setTechnology("");
              setSeverity("");
              setDateFrom("");
              setDateTo("");
            }}
          >
            Reset
          </button>
        </div>

        <div className="table-wrapper">
          <table className="anomaly-table">
            <thead>
              <tr>
                <th>Site</th>
                <th>Region</th>
                <th>Technology</th>
                <th>Detected</th>
                <th>Main KPI</th>
                <th>Severity</th>
                <th>Explanation</th>
              </tr>
            </thead>

            <tbody>
              {anomalies.slice(0, 20).map((anomaly) => (
                <tr key={anomaly.detection_id}>
                  <td>
                    <strong>{anomaly.site_id}</strong>
                    <div className="site-name">{anomaly.site_name}</div>
                  </td>

                  <td>{anomaly.region}</td>
                  <td>{anomaly.technology}</td>
                  <td>{anomaly.timestamp}</td>
                  <td>{anomaly.main_kpi}</td>

                  <td>
                    <span
                      className={`severity-badge ${anomaly.severity.toLowerCase()}`}
                    >
                      {anomaly.severity}
                    </span>
                  </td>

                  <td className="explanation">{anomaly.explanation}</td>
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