from typing import Generator, Any

import requests

from services.evaluators.base import BaseExecutionNode, ContextData, StreamableMessage, TestScenariosMessage
from services.evaluators.connectivity import DriverAccessNode, AccessCheckNode
from services.evaluators.html.parser import HtmlParsingNode
from services.llm.agents import invoke_scenario_generation_agent
from services.llm.models import DEFAULT_MODEL
import bs4

MAX_CONTENT_LENGTH = 1000


class TestScenarioGenerationNode(BaseExecutionNode, node_name="scenario_generation"):
    __dependencies__ = (DriverAccessNode, HtmlParsingNode)

    def _evaluate_impl(
        self, *args, context: ContextData = None, **kwargs
    ) -> Generator[StreamableMessage, None, Any]:
        if not context.driver.current_url.endswith(
            context.url
        ):  # (Heuristic to reload page if URL has changed)
            context.driver.get(context.url)  # Reload URL if necessary
        soup: bs4.BeautifulSoup = context.history[HtmlParsingNode.node_name].value

        text_content = soup.get_text(strip=True)[:MAX_CONTENT_LENGTH]
        result = invoke_scenario_generation_agent(
            driver=context.driver,
            url=context.url,
            title=context.driver.title,
            content=text_content,
            model=DEFAULT_MODEL,
        )

        yield TestScenariosMessage(
            message=f"Generated {len(result.scenarios)} scenarios.", level="success", details=result
        )

        return result
