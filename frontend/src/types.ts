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
  | "metrics"
  | "test_execution_report";

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

export interface TestExecutionResult {
  scenario_name: string;
  status: string;
  execution_details: string;
  errors_encountered?: string[];
  execution_time_seconds?: number;
}

export interface TestExecutionReport {
  total_scenarios: number;
  passed: number;
  failed: number;
  errors: number;
  results: TestExecutionResult[];
}

export interface StateDetails {
  agent_id?: string;
  agent_name?: string;
  scenario_id?: string;
  scenario_name?: string;
  is_end_state?: boolean;
}

export interface StreamableMessage {
  agent_id?: string;
  agent_name?: string
  scenario_id?: string;
  scenario_name?: string;
  message: string;
  source: MessageSource;
  type: MessageType;
  level: MessageLevel;
  details?: TestScenarioList | Metric | MetricsList | StateDetails | TestExecutionReport | any;
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
  executionReport?: TestExecutionReport;
}

export interface ScenarioState {
  id: string;
  name: string;
  messages: StreamableMessage[];
  isActive: boolean;
  isComplete: boolean;
}
