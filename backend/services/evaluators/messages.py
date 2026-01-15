import datetime
from functools import partial
from typing import Literal, Any

from pydantic import BaseModel, Field

from services.llm.agents import TestExecutionReport


class StreamableMessage(BaseModel):
    """
    Represents a streamable message streamed to the client.

    This class is used for transferring messages related to evaluations, state
    management, feedback, tests, and other system metrics. It contains metadata
    associated with the message, such as its source, type, and severity level,
    as well as optional additional details and a timestamp.
    """
    agent_id: str | None = None
    agent_name : str | None = None
    scenario_id: str | None = None
    scenario_name: str | None = None
    message: str
    source: Literal["agent", "orchestrator"] = "agent"
    type: Literal["evaluation","state","feedback", "test_scenarios", "metrics", "test_execution_report"] = "evaluation"
    level: Literal[
        "info", "improvement", "warning", "error",
        "bug", "vulnerability", "malicious", "success"
    ] = "info"
    details: Any = None
    timestamp: datetime.datetime = Field(default_factory=partial(datetime.datetime.now,tz=datetime.timezone.utc))


class StateDetails(BaseModel):
    """
    Represents the details of a state's current context within an agent and scenario.

    This class is used to store and manage details about a specific state,
    including the associated agent and scenario IDs. It also tracks whether
    the state is an end state in the sequence.
    """
    agent_id : str | None = None
    agent_name : str | None = None
    scenario_id : str | None = None
    scenario_name : str | None = None
    is_end_state : bool = False


class OrchestratorStateMessage(StreamableMessage):
    """
    Represents a message describing the state of an orchestrator.

    This class is a specific type of `StreamableMessage` used to convey information
    about the state of an orchestrator. It includes a fixed source and type to
    identify the message as being specific to the orchestrator's state, along with
    optional details provided in a `StateDetails` object.
    """
    source : Literal["orchestrator"] = "orchestrator"
    type: Literal["state"] = "state"
    details: StateDetails | None = None


class AgentAssessmentMessage(StreamableMessage):
    source : Literal["agent"] = "agent"


class TestScenariosMessage(StreamableMessage):
    """
    Represents a message specifically for test scenarios.

    This class is a streamable message used to facilitate communication
    involving the generated test scenarios.
    """
    source : Literal["agent"] = "agent"
    type: Literal["test_scenarios"] = "test_scenarios"


class Metric(BaseModel):
    """
    Represents a metric for evaluation purposes.

    This class encapsulates a metric with a name, score, and optional feedback, issues, and improvements.
    """
    name: str
    score: int | None = None
    feedback: str | None = None
    issues: list[str] | None = None
    improvements: list[str] | None = None


class MetricsList(BaseModel):
    """
    Represents a list of metrics with associated metadata.

    This class is used to encapsulate a collection of metrics along with relevant
    metadata such as name, feedback, and a score. It is commonly employed in
    contexts where metrics are analyzed and tracked alongside optional descriptive
    feedback and scoring.
    """
    name : str | None = None
    metrics: list[Metric]
    feedback: str | None = None
    score: int | None = None


class MetricsMessage(StreamableMessage):
    """
    Represents a message containing metrics information.

    The MetricsMessage class is used to encapsulate metric-related information
    that is streamed or processed within a system. It specifies the source and
    type of the message and contains detailed metric data.Z
    """
    source : Literal["agent"] = "agent"
    type: Literal["metrics"] = "metrics"
    details : Metric | MetricsList


class TestExecutionReportMessage(StreamableMessage):
    source : Literal["agent"] = "agent"
    type: Literal["test_execution_report"] = "test_execution_report"
    details : TestExecutionReport