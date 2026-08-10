import { useEffect, useMemo, useState } from "react";
import "./App.css";

type Summary = {
  total_sites: number;
  total_anomalies: number;
  critical_anomalies: number;
  most_common_problem: string | null;
  latest_measurement_time: string | null;
};

type Anomaly = {
  event_id: string;
  site_id: string;
  site_name: string;
  region: string;
  technology: string;
  timestamp: string;
  anomaly_type: string;
  severity: string;
};

function App() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  const [region, setRegion] = useState("");
  const [technology, setTechnology] = useState("");
  const [severity, setSeverity] = useState("");

  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/summary")
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

    const queryString = params.toString();

    const url = queryString
      ? `http://127.0.0.1:8000/api/anomalies?${queryString}`
      : "http://127.0.0.1:8000/api/anomalies";

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
  }, [region, technology, severity]);

  const regions = useMemo(() => {
    return Array.from(
      new Set(anomalies.map((anomaly) => anomaly.region))
    ).sort();
  }, [anomalies]);

  const technologies = useMemo(() => {
    return Array.from(
      new Set(anomalies.map((anomaly) => anomaly.technology))
    ).sort();
  }, [anomalies]);

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
          <h2>Anomalies</h2>
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
          <h2>Recent Anomalies</h2>
          <span>{anomalies.length} records</span>
        </div>

        <div className="filters">
          <label>
            Region
            <select
              value={region}
              onChange={(event) => setRegion(event.target.value)}
            >
              <option value="">All</option>

              {regions.map((item) => (
                <option key={item} value={item}>
                  {item}
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

          <button
            className="reset-button"
            onClick={() => {
              setRegion("");
              setTechnology("");
              setSeverity("");
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
                <th>Time</th>
                <th>Anomaly Type</th>
                <th>Severity</th>
              </tr>
            </thead>

            <tbody>
              {anomalies.slice(0, 20).map((anomaly) => (
                <tr key={anomaly.event_id}>
                  <td>
                    <strong>{anomaly.site_id}</strong>
                    <div className="site-name">{anomaly.site_name}</div>
                  </td>

                  <td>{anomaly.region}</td>
                  <td>{anomaly.technology}</td>
                  <td>{anomaly.timestamp}</td>
                  <td>{anomaly.anomaly_type}</td>

                  <td>
                    <span
                      className={`severity-badge ${anomaly.severity.toLowerCase()}`}
                    >
                      {anomaly.severity}
                    </span>
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




