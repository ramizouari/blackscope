export type MessageLevel =
  | "info"
  | "improvement"
  | "warning"
  | "error"
  | "bug"
  | "vulnerability"
  | "malicious"
  | "success";

export type MessageType =
  | "evaluation"
  | "state"
  | "feedback"
  | "test_scenarios"
  | "metrics";

export type MessageSource = "agent" | "orchestrator";

export interface TestScenario {
  short_name: string;
  name: string;
  objective: string;
  steps: string[];
  expected_result: string;
  preconditions?: string;
}

export interface TestScenarioList {
  scenarios: TestScenario[];
}

export interface Metric {
  name: string;
  score?: number;
  feedback?: string;
  issues?: string[];
  improvements?: string[];
}

export interface MetricsList {
  name?: string;
  metrics: Metric[];
  feedback?: string;
  score?: number;
}

export interface StateDetails {
  agent_id?: string;
  scenario_id?: string;
  is_end_state?: boolean;
}

export interface StreamableMessage {
  agent_id?: string;
  scenario_id?: string;
  message: string;
  source: MessageSource;
  type: MessageType;
  level: MessageLevel;
  details?: TestScenarioList | Metric | MetricsList | StateDetails | any;
  timestamp: string;
}

export interface UpdateMessage {
  type: string;
  content: StreamableMessage;
}

export interface AgentState {
  id: string;
  name: string;
  messages: StreamableMessage[];
  scenarios: Map<string, ScenarioState>;
  isActive: boolean;
  isComplete: boolean;
  testScenarios?: TestScenario[];
  metrics?: Metric | MetricsList;
}

export interface ScenarioState {
  id: string;
  name: string;
  messages: StreamableMessage[];
  isActive: boolean;
  isComplete: boolean;
}
