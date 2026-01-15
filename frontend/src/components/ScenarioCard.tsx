import type { ScenarioState } from "../types";
import MessageItem from "./MessageItem";
import "./ScenarioCard.css";

interface ScenarioCardProps {
  scenario: ScenarioState;
}

function ScenarioCard({ scenario }: ScenarioCardProps) {
  return (
    <div className={`scenario-card ${scenario.isActive ? "active" : ""}`}>
      <div className="scenario-header">
        <div className="scenario-name-wrapper">
          {scenario.isActive && <span className="execution-icon">▶</span>}
          <h5>{scenario.name}</h5>
        </div>
        <div className="scenario-badges">
          {scenario.isActive && <span className="status-badge active">Running</span>}
          {scenario.isComplete && !scenario.isActive && <span className="status-badge complete">Done</span>}
        </div>
      </div>

      <div className="scenario-body">
        {scenario.messages.map((message, idx) => (
          <MessageItem key={idx} message={message} />
        ))}
      </div>
    </div>
  );
}

export default ScenarioCard;
