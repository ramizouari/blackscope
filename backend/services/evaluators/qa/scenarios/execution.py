from typing import Generator, Literal

from services.evaluators.base import BaseExecutionNode, ContextData
from services.evaluators.messages import StreamableMessage, StateDetails, OrchestratorStateMessage, \
    AgentAssessmentMessage, TestExecutionReportMessage
from services.evaluators.connectivity import DriverAccessNode
from services.evaluators.qa.scenarios.generation import TestScenarioGenerationNode
from services.llm.agents import (
    invoke_scenario_execution_agent,
    TestExecutionResult,
    TestExecutionReport,
    TestScenarioList,
)
from services.llm.models import DEFAULT_MODEL

class TestScenarioExecutionNode(BaseExecutionNode, node_name="scenario_execution"):
    """
    Handles the execution of test scenarios within a specific execution context.

    This class is responsible for coordinating the execution of test scenarios as
    part of a testing workflow. It ensures that scenarios are executed in sequence
    and analyzes their outcomes to produce a detailed execution report. The class
    relies on dependencies like `DriverAccessNode` and `TestScenarioGenerationNode`
    to fetch necessary data and interact with the test execution environment.
    """
    __dependencies__ = (DriverAccessNode, TestScenarioGenerationNode)

    def _evaluate_impl(
        self, *args, context: ContextData = None, **kwargs
    ) -> Generator[StreamableMessage, None, TestExecutionReport]:
        if not context.driver.current_url.endswith(
            context.url
        ):  # (Heuristic to reload page if URL has changed)
            context.driver.get(context.url)  # Reload URL if necessary

        results = []
        passed = 0
        failed = 0
        errors = 0

        scenarios_list: TestScenarioList = context.history[
            TestScenarioGenerationNode.node_name
        ].value

        for scenario in scenarios_list.scenarios:
            try:
                yield OrchestratorStateMessage(
                    message=f"Executing scenario {scenario.name}...",
                    details=StateDetails(
                        agent_id=self.node_name,
                        agent_name=self.full_name,
                        scenario_id=scenario.short_name,
                        scenario_name=scenario.name
                    ),
                   )
                result = invoke_scenario_execution_agent(
                    context.driver, scenario, context.url, DEFAULT_MODEL
                )
                results.append(result)
                level: Literal["error", "success"] = "error"
                if result.status == "PASSED":
                    passed += 1
                    level = "success"
                elif result.status == "FAILED":
                    failed += 1
                elif result.status == "ERROR":
                    errors += 1
                yield StreamableMessage(
                    message=result.execution_details,
                    level="info",
                    scenario_id=scenario.short_name,
                    scenario_name=scenario.name,
                )
                yield AgentAssessmentMessage(
                    message=f"Scenario {scenario.name} completed: {result.status}", level=level,
                    scenario_id=scenario.short_name,
                    scenario_name=scenario.name,
                )

            except Exception as e:
                # If execution completely fails, create an error result
                yield AgentAssessmentMessage(
                    message=f"A crash occurred during scenario {scenario.name}.", level="error",
                    scenario_id=scenario.short_name
                )
                error_result = TestExecutionResult(
                    scenario_name=scenario.name,
                    status="ERROR",
                    execution_details=f"Failed to execute scenario: {str(e)}",
                    errors_encountered=[str(e)],
                )
                results.append(error_result)
                errors += 1

        final_report=TestExecutionReport(
            total_scenarios=len(scenarios_list.scenarios),
            passed=passed,
            failed=failed,
            errors=errors,
            results=results,
        )

        yield TestExecutionReportMessage(
            message="Test Scenario Execution Complete.", details=final_report
        )
        return final_report

    @property
    def full_name(self):
        return "Test Scenario Execution"