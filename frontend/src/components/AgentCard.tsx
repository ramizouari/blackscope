import type { AgentState } from "../types";
import MessageItem from "./MessageItem";
import ScenarioCard from "./ScenarioCard";
import TestScenarioList from "./TestScenarioList";
import MetricsDisplay from "./MetricsDisplay";
import { RotatingLines } from "react-loader-spinner";


import "./AgentCard.css";

interface AgentCardProps {
  agent: AgentState;
}

function AgentCard({ agent }: AgentCardProps) {
  const scenarioArray = Array.from(agent.scenarios.values());
  const hasScenarios = scenarioArray.length > 0;

  return (
    <div className={`agent-card ${agent.isActive ? "active" : ""}`}>
      <div className="agent-header">
        <div className="agent-title">
          <div className="agent-name-wrapper">
            {agent.isActive && <RotatingLines
                strokeColor="grey"
                strokeWidth="5"
                animationDuration="0.75"
                width="96"
                visible={true}
            />}
            <h3>{agent.name}</h3>
          </div>
          <div className="status-badges">
            {agent.isActive && <span className="status-badge active">Active</span>}
            {agent.isComplete && !agent.isActive && <span className="status-badge complete">Complete</span>}
          </div>
        </div>
      </div>

      <div className="agent-body">
        {agent.messages.length > 0 && (
          <div className="messages-section">
            {agent.messages.map((message, idx) => (
              <MessageItem key={idx} message={message} />
            ))}
          </div>
        )}

        {agent.testScenarios && agent.testScenarios.length > 0 && (
          <TestScenarioList scenarios={agent.testScenarios} />
        )}

        {agent.metrics && <MetricsDisplay metrics={agent.metrics} />}

        {hasScenarios && (
          <div className="scenarios-section">
            <h4 className="scenarios-title">Test Scenarios</h4>
            <div className="scenarios-container">
              {scenarioArray.map((scenario) => (
                <ScenarioCard key={scenario.id} scenario={scenario} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentCard;
