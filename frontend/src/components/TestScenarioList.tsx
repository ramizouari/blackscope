import type { TestScenario } from "../types";
import "./TestScenarioList.css";

interface TestScenarioListProps {
  scenarios: TestScenario[];
}

function TestScenarioList({ scenarios }: TestScenarioListProps) {
  return (
    <div className="test-scenario-list">
      <h4 className="section-title">Generated Test Scenarios</h4>
      <div className="scenarios-grid">
        {scenarios.map((scenario, idx) => (
          <div key={idx} className="test-scenario-item">
            <div className="scenario-name">{scenario.name}</div>
            <div className="scenario-objective">
              <strong>Objective:</strong> {scenario.objective}
            </div>
            {scenario.preconditions && (
              <div className="scenario-preconditions">
                <strong>Preconditions:</strong> {scenario.preconditions}
              </div>
            )}
            <div className="scenario-steps">
              <strong>Steps:</strong>
              <ol>
                {scenario.steps.map((step, stepIdx) => (
                  <li key={stepIdx}>{step}</li>
                ))}
              </ol>
            </div>
            <div className="scenario-expected">
              <strong>Expected Result:</strong> {scenario.expected_result}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TestScenarioList;
