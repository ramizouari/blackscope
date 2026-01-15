import type { TestExecutionReport } from "../types";
import "./TestExecutionReportTable.css";

interface TestExecutionReportTableProps {
  report: TestExecutionReport;
}

function TestExecutionReportTable({ report }: TestExecutionReportTableProps) {
  const getStatusClass = (status: string) => {
    switch (status.toUpperCase()) {
      case "PASSED":
        return "status-passed";
      case "FAILED":
        return "status-failed";
      case "ERROR":
        return "status-error";
      default:
        return "";
    }
  };

  return (
    <div className="test-execution-report">
      <h4 className="report-title">Test Execution Report</h4>

      <div className="report-summary">
        <div className="summary-item">
          <span className="summary-label">Total:</span>
          <span className="summary-value">{report.total_scenarios}</span>
        </div>
        <div className="summary-item passed">
          <span className="summary-label">Passed:</span>
          <span className="summary-value">{report.passed}</span>
        </div>
        <div className="summary-item failed">
          <span className="summary-label">Failed:</span>
          <span className="summary-value">{report.failed}</span>
        </div>
        <div className="summary-item error">
          <span className="summary-label">Errors:</span>
          <span className="summary-value">{report.errors}</span>
        </div>
      </div>

      <div className="report-table-container">
        <table className="report-table">
          <thead>
            <tr>
              <th>Scenario</th>
              <th>Status</th>
              <th>Details</th>
              <th>Errors</th>
              <th>Time (s)</th>
            </tr>
          </thead>
          <tbody>
            {report.results.map((result, idx) => (
              <tr key={idx} className={getStatusClass(result.status)}>
                <td className="scenario-name">{result.scenario_name}</td>
                <td className="status-cell">
                  <span className={`status-badge ${getStatusClass(result.status)}`}>
                    {result.status}
                  </span>
                </td>
                <td className="details-cell">{result.execution_details}</td>
                <td className="errors-cell">
                  {result.errors_encountered && result.errors_encountered.length > 0 ? (
                    <ul className="error-list">
                      {result.errors_encountered.map((error, errorIdx) => (
                        <li key={errorIdx}>{error}</li>
                      ))}
                    </ul>
                  ) : (
                    <span className="no-errors">-</span>
                  )}
                </td>
                <td className="time-cell">
                  {result.execution_time_seconds !== undefined
                    ? result.execution_time_seconds.toFixed(2)
                    : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TestExecutionReportTable;
