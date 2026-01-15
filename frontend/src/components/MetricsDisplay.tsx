import type { Metric, MetricsList } from "../types";
import "./MetricsDisplay.css";

interface MetricsDisplayProps {
  metrics: Metric | MetricsList;
}

function MetricsDisplay({ metrics }: MetricsDisplayProps) {
  const isMetricsList = "metrics" in metrics;

  if (isMetricsList) {
    const metricsList = metrics as MetricsList;
    return (
      <div className="metrics-display">
        <h4 className="section-title">
          {metricsList.name || "Metrics Report"}
        </h4>
        {metricsList.score !== undefined && (
          <div className="overall-score">
            Score: <strong>{metricsList.score}</strong>
          </div>
        )}
        {metricsList.feedback && (
          <div className="overall-feedback">{metricsList.feedback}</div>
        )}
        <div className="metrics-list">
          {metricsList.metrics.map((metric, idx) => (
            <MetricItem key={idx} metric={metric} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="metrics-display">
      <h4 className="section-title">Metric</h4>
      <MetricItem metric={metrics as Metric} />
    </div>
  );
}

function MetricItem({ metric }: { metric: Metric }) {
  return (
    <div className="metric-item">
      <div className="metric-header">
        <span className="metric-name">{metric.name}</span>
        {metric.score !== undefined && (
          <span className="metric-score">{metric.score}</span>
        )}
      </div>
      {metric.feedback && <div className="metric-feedback">{metric.feedback}</div>}
      {metric.issues && metric.issues.length > 0 && (
        <div className="metric-issues">
          <strong>Issues:</strong>
          <ul>
            {metric.issues.map((issue, idx) => (
              <li key={idx}>{issue}</li>
            ))}
          </ul>
        </div>
      )}
      {metric.improvements && metric.improvements.length > 0 && (
        <div className="metric-improvements">
          <strong>Improvements:</strong>
          <ul>
            {metric.improvements.map((improvement, idx) => (
              <li key={idx}>{improvement}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default MetricsDisplay;
