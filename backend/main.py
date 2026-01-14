from fastapi import FastAPI
from fastapi.responses import Response, StreamingResponse
from fastapi import status
import requests
import json

from openai import BaseModel

from services.evaluators.base import Orchestrator, StreamableMessage
from services.evaluators.connectivity import AccessCheckNode, DriverAccessNode
from services.evaluators.drivers import create_headless_firefox_driver
from services.evaluators.html.compliance import HtmlComplianceNode
from services.evaluators.html.parser import HtmlParsingNode
from services.evaluators.qa.execution import TestScenarioExecutionNode
from services.evaluators.qa.generation import TestScenarioGenerationNode


class UrlRequest(BaseModel):
    url: str


class UpdateMessage(BaseModel):
    type: str
    content: StreamableMessage


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/qa")
async def provide_qa(url: UrlRequest):
    """
    Generate Q/A assessment for a given URL.
    """

    def generate():
        connector = AccessCheckNode()
        html_parsing = HtmlParsingNode()
        html_compliance = HtmlComplianceNode()
        test_scenario_generation = TestScenarioGenerationNode()
        test_scenario_execution = TestScenarioExecutionNode()
        driver_access = DriverAccessNode()
        orch = Orchestrator(
            [
                connector,
                driver_access,
                html_parsing,
                html_compliance,
                test_scenario_generation,
                test_scenario_execution,
            ]
        )

        with requests.Session() as session, create_headless_firefox_driver() as driver:
            session.headers.update(
                {
                    "User-Agent": "HTML-QA/0.1",
                    "Accept": "text/html,application/xhtml+xml,application/xml",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
            for msg in orch.evaluate(url.url, session, driver):
                yield UpdateMessage(type="update", content=msg).model_dump_json() + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.get("/heartbeat")
async def heartbeat():
    return Response(status_code=status.HTTP_200_OK)


@app.get("/health")
async def health():
    return {"status": "UP"}
