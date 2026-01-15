from typing import Generator, Literal

from services.evaluators.base import BaseExecutionNode, ContextData
from services.evaluators.messages import StreamableMessage, AgentAssessmentMessage, Metric, MetricsList, MetricsMessage
from services.evaluators.connectivity import DriverAccessNode
from services.evaluators.qa.scenarios.generation import TestScenarioGenerationNode
from services.llm.agents import (
    TestExecutionReport,
    invoke_ui_analyzer_agent, UIQualityAssessment,
)
from services.llm.models import DEFAULT_MODEL, DEFAULT_VL_MODEL, get_vl_model


class UIAnalyzerNode(BaseExecutionNode, node_name="ui_analyzer"):
    """
    Class for analyzing UI quality and providing assessments.

    This class is designed to execute a UI quality assessment using an underlying driver
    and a preconfigured UI analysis model. It evaluates the current state of a webpage
    and extracts relevant quality metrics, including category-specific scores, feedback,
    and issues. The functionality ensures consistency of the URL within the driver and
    reloads the page when necessary, providing high accuracy in assessment results.
    """
    __dependencies__ = (DriverAccessNode,)

    def _evaluate_impl(
        self, *args, context: ContextData = None, **kwargs
    ) -> Generator[StreamableMessage, None, UIQualityAssessment]:
        if not context.driver.current_url.endswith(
            context.url
        ):  # (Heuristic to reload page if URL has changed)
            context.driver.get(context.url)  # Reload URL if necessary

        results=invoke_ui_analyzer_agent(context.driver, vl_model=get_vl_model(),model=DEFAULT_MODEL)
        yield MetricsMessage(
            message="UI Quality Assessment",
            details=MetricsList(
                name="UI Quality Assessment",
                metrics=[
                    Metric(
                        name=element.category,
                        score=element.score,
                        feedback=element.feedback,
                        issues=element.issues
                    ) for element in results.categories
                ],
                score=results.overall_score, feedback=results.overall_feedback,
            )
        )
        return results

    @property
    def full_name(self):
        return "UI Quality Assessment"