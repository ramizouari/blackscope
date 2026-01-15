import { useState } from "react";
import "./App.css";
import URLForm from "./components/URLForm";
import AgentDashboard from "./components/AgentDashboard";
import type {AgentState, MetricsList, StateDetails, StreamableMessage, TestExecutionReport, TestScenarioList, UpdateMessage} from "./types";

function App() {
  const [agents, setAgents] = useState<Map<string, AgentState>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  const handleSubmit = async (url: string) => {
    setAgents(new Map());
    setError(null);
    setIsLoading(true);
    setIsComplete(false);

    const backendHost = import.meta.env.VITE_BACKEND_HOST || "http://localhost:8000";

    try {
      const response = await fetch(`${backendHost}/qa`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response body");
      }

      let remainingChunk = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          // Stream ended without formal completion
          if (!isComplete) {
            setError("Stream ended unexpectedly - server disconnected");
            setIsLoading(false);
          }
          break;
        }

        const chunk = decoder.decode(value);
        const skipLastLine = chunk.at(chunk.length - 1) !== "\n"

        const lines = chunk.split("\n").filter((line) => line.trim());
        if(remainingChunk.length > 0)
          lines[0] = remainingChunk + lines[0];
        if(skipLastLine)
          remainingChunk = lines.pop() ?? "";

        for (const line of lines) {
          try {
            const update: UpdateMessage = JSON.parse(line);
            const message: StreamableMessage = update.content;

            setAgents((prevAgents) => {
              const newAgents = new Map(prevAgents);
              const agentId = message.agent_id || "orchestrator";

              let agent = newAgents.get(agentId);
              if (!agent) {
                agent = {
                  id: agentId,
                  name: message.agent_name ?? agentId,
                  messages: [],
                  scenarios: new Map(),
                  isActive: true,
                  isComplete: false,
                };
                newAgents.set(agentId, agent);
              }

              // Handle state messages
              if (message.type === "state" && message.details) {
                const details = message.details as StateDetails;
                if (details.is_end_state) {
                  // Formal completion - mark all agents as inactive
                  newAgents.forEach((a) => {
                    a.isActive = false;
                    a.isComplete = true;
                  });
                  setIsComplete(true);
                  setIsLoading(false);
                } else if (details.agent_id) {
                  // Mark previous agent as inactive and complete
                  newAgents.forEach((a) => {
                    if (a.isActive && a.id !== details.agent_id) {
                      a.isActive = false;
                      a.isComplete = true;
                    }
                  });

                  // Mark agent as active
                  const targetAgent = newAgents.get(details.agent_id);
                  if (targetAgent) {
                    targetAgent.isActive = true;
                  }
                  if (details.scenario_id) {
                    // Mark scenario as active
                    if (targetAgent) {
                      let scenario = targetAgent.scenarios.get(
                        details.scenario_id
                      );
                      if (!scenario) {
                        scenario = {
                          id: details.scenario_id,
                          name: details.scenario_name ?? details.scenario_id,
                          messages: [],
                          isActive: true,
                          isComplete: false,
                        };
                        targetAgent.scenarios.set(details.scenario_id, scenario);
                      } else {
                        scenario.isActive = true;
                      }
                    }
                  }
                }
              }

              // Handle test scenarios message
              if (message.type === "test_scenarios" && message.details) {
                const scenarioList = message.details as TestScenarioList;
                agent.testScenarios = scenarioList.scenarios || [];
              }

              // Handle metrics message
              if (message.type === "metrics" && message.details) {
                agent.metrics = message.details as MetricsList;
              }

              // Handle test execution report message
              if (message.type === "test_execution_report" && message.details) {
                agent.executionReport = message.details as TestExecutionReport;
              }

              // Add message to agent or scenario
              if (message.scenario_id) {
                let scenario = agent.scenarios.get(message.scenario_id);
                if (!scenario) {
                  scenario = {
                    id: message.scenario_id,
                    name: message.scenario_id,
                    messages: [],
                    isActive: false,
                    isComplete: false,
                  };
                  agent.scenarios.set(message.scenario_id, scenario);
                }
                scenario.messages.push(message);

                // Mark scenario as complete if it has a success or error message
                if (message.level === "success" || message.level === "error") {
                  scenario.isActive = false;
                  scenario.isComplete = true;
                }
              } else {
                agent.messages.push(message);
              }

              return newAgents;
            });
          } catch (e) {
            console.error("Failed to parse message:", e, line);
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Blackscope</h1>
        <p>Analyze websites with automated quality assurance agents</p>
      </header>

      <URLForm onSubmit={handleSubmit} isLoading={isLoading} />

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {agents.size > 0 && (
        <AgentDashboard agents={agents} isComplete={isComplete} />
      )}
    </div>
  );
}

export default App;
