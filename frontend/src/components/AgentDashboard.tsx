import type { AgentState } from "../types";
import AgentCard from "./AgentCard";
import MessageLegend from "./MessageLegend";
import "./AgentDashboard.css";

interface AgentDashboardProps {
  agents: Map<string, AgentState>;
  isComplete: boolean;
}

function AgentDashboard({ agents, isComplete }: AgentDashboardProps) {
  const agentArray = Array.from(agents.values()).filter(
    (agent) => agent.id !== "orchestrator"
  );

  return (
    <div className="agent-dashboard">
      <div className="dashboard-header">
        <h2>Assessment Progress</h2>
        {isComplete && (
          <span className="completion-badge">✓ Complete</span>
        )}
      </div>

      <MessageLegend />

      <div className="agents-container">
        {agentArray.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  );
}

export default AgentDashboard;
