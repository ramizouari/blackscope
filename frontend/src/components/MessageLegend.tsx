import { useState } from "react";
import "./MessageLegend.css";

function MessageLegend() {
  const [isExpanded, setIsExpanded] = useState(false);

  const legendItems = [
    { level: "success", icon: "✓", label: "Success", description: "Operation completed successfully" },
    { level: "error", icon: "✗", label: "Error", description: "Critical error occurred" },
    { level: "warning", icon: "⚠", label: "Warning", description: "Potential issue detected" },
    { level: "info", icon: "ℹ", label: "Info", description: "General information" },
    { level: "improvement", icon: "→", label: "Improvement", description: "Suggested enhancement" },
    { level: "bug", icon: "✗", label: "Bug", description: "Bug detected" },
    { level: "vulnerability", icon: "🔒", label: "Vulnerability", description: "Security issue" },
    { level: "malicious", icon: "⚡", label: "Malicious", description: "Potentially harmful content" },
  ];

  return (
    <div className="message-legend">
      <button
        className="legend-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-label="Toggle message legend"
      >
        <span className="legend-icon">ℹ</span>
        <span className="legend-text">Message Legend</span>
        <span className={`legend-arrow ${isExpanded ? "expanded" : ""}`}>▼</span>
      </button>

      {isExpanded && (
        <div className="legend-content">
          <div className="legend-grid">
            {legendItems.map((item) => (
              <div key={item.level} className={`legend-item level-${item.level}`}>
                <span className="legend-item-icon">{item.icon}</span>
                <div className="legend-item-text">
                  <strong>{item.label}</strong>
                  <span className="legend-item-description">{item.description}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default MessageLegend;
