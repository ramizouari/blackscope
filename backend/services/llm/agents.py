from typing import List, Optional, cast

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from selenium.webdriver.remote.webdriver import WebDriver

from .models import get_vl_model, DEFAULT_MODEL
from .prompt_manager import get_prompt_manager
import time
import io
import base64
from PIL import Image

from services.llm.tools import get_selenium_tools, SeleniumGetPageContentTool


class TestScenario(BaseModel):
    """Represents a single test scenario"""
    short_name : str = Field(description="Short name for the scenario")
    name: str = Field(description="The name/title of the scenario")
    objective: str = Field(description="What this scenario tests")
    steps: List[str] = Field(description="User actions to perform")
    expected_result: str = Field(description="What should happen")
    preconditions: Optional[str] = Field(
        default=None, description="Any setup needed before the test"
    )


class TestScenarioList(BaseModel):
    """Collection of test scenarios"""

    scenarios: List[TestScenario] = Field(description="List of test scenarios")


def create_scenario_generation_prompt(
    url: str, title: str, content: str, max_length: int = 5000
) -> str:
    """
    Create a prompt for generating test scenarios for a visited web page.

    Args:
        url: The URL of the web page
        title: The page title
        content: The page content (can be HTML or visible text)
        max_length: Maximum length of the generated prompt, after truncation if needed

    Returns:
        A formatted prompt string
    """

    # Truncate content if too long (keep first 5000 characters)
    truncated_content = content[:max_length] + "..." if len(content) > max_length else content

    prompt_manager = get_prompt_manager()
    return prompt_manager.render(
        "generate_scenarios.j2", url=url, title=title, content=truncated_content
    )


def invoke_scenario_generation_agent(
    driver: WebDriver,
    url: str,
    title: str,
    content: str,
    model: BaseChatModel | str,
    tools: list[BaseTool] = None,
):
    """
    Create a Langchain agent for generating test scenarios from web pages.

    This agent combines Selenium browsing tools with an LLM to navigate web pages,
    extract content, and generate comprehensive test scenarios.

    Args:
        llm: A Langchain LLM instance (e.g., ChatOpenAI, ChatAnthropic, etc.)
        driver: Selenium WebDriver instance to use for browsing
        tools: Optional list of additional tools to include in the agent

    Returns:
        A Langchain AgentExecutor configured with Selenium tools
    """
    if isinstance(model, str):
        model = init_chat_model(model)

    # Create the agent prompt
    prompt_manager = get_prompt_manager()
    system_message = prompt_manager.render("scenario_generation_system.j2")

    prompt = create_scenario_generation_prompt(url=url, title=title, content=content)
    default_tools = [
        t for t in get_selenium_tools(driver) if not isinstance(t, SeleniumGetPageContentTool)
    ]
    agent = create_agent(
        model=model,
        tools=tools or default_tools,
        system_prompt="You are a helpful assistant",
        debug=True,
    )
    driver.get(url)  # Forwards to URL as initial state
    # Run the agent
    result = agent.invoke(
        {"messages": [SystemMessage(content=system_message), HumanMessage(content=prompt)]}
    )

    # Extract the message content from the agent result
    agent_message = result["messages"][-1].content if "messages" in result else str(result)

    # Parse the unstructured response into structured output
    structured_result = parse_scenarios_to_structured_output(model, agent_message)

    return structured_result


def parse_scenarios_to_structured_output(model, scenario_text: str) -> TestScenarioList:
    """
    Parse the LLM-generated scenario text into structured Pydantic output.

    Args:
        model: A Langchain LLM instance with structured output support
        scenario_text: The unstructured text containing test scenarios

    Returns:
        TestScenarioList: A structured collection of test scenarios
    """
    structured_llm = model.with_structured_output(TestScenarioList)

    prompt_manager = get_prompt_manager()
    parsing_prompt = prompt_manager.render("parse_scenarios.j2", scenario_text=scenario_text)

    result = structured_llm.invoke(parsing_prompt)
    return result


class TestExecutionResult(BaseModel):
    """Result of executing a single test scenario"""

    scenario_name: str = Field(description="Name of the executed scenario")
    status: str = Field(description="Test status: PASSED, FAILED, or ERROR")
    execution_details: str = Field(description="Details about what happened during execution")
    errors_encountered: Optional[List[str]] = Field(
        default=None, description="List of errors encountered"
    )
    screenshots: Optional[List[str]] = Field(
        default=None, description="Paths to screenshots taken during test"
    )
    execution_time_seconds: Optional[float] = Field(
        default=None, description="Time taken to execute the test"
    )


def invoke_scenario_execution_agent(
    driver: WebDriver,
    scenario: TestScenario,
    url: str,
    model: BaseChatModel | str,
    tools: list[BaseTool] = None,
) -> TestExecutionResult:
    """
    Execute a test scenario using Selenium and LLM agent.

    This agent takes a structured test scenario, executes it step by step using Selenium tools,
    and reports whether the test passed or failed.

    Args:
        driver: Selenium WebDriver instance to use for browsing
        scenario: The TestScenario object to execute
        url: The base URL to test against
        model: A Langchain LLM instance (e.g., ChatOpenAI, ChatAnthropic, etc.)
        tools: Optional list of additional tools to include in the agent
    Returns:
        TestExecutionResult: Structured result of the test execution

    """

    if isinstance(model, str):
        model = init_chat_model(model)

    start_time = time.time()

    # Create the system message for the execution agent
    prompt_manager = get_prompt_manager()
    system_message = prompt_manager.render("scenario_execution_system.j2")

    # Create the execution prompt
    execution_prompt = prompt_manager.render(
        "scenario_execution_prompt.j2",
        scenario_name=scenario.name,
        objective=scenario.objective,
        preconditions=scenario.preconditions,
        url=url,
        steps=scenario.steps,
        expected_result=scenario.expected_result
    )

    # Create the agent
    agent = create_agent(
        model=model,
        tools=tools or get_selenium_tools(driver),
        system_prompt="You are a test execution agent",
    )

    # Navigate to the URL as initial state
    driver.get(url)

    # Run the agent to execute the test
    result = agent.invoke(
        {
            "messages": [
                SystemMessage(content=system_message),
                HumanMessage(content=execution_prompt),
            ]
        }
    )

    execution_time = time.time() - start_time

    # Extract the execution report from the agent
    agent_message = result["messages"][-1].content if "messages" in result else str(result)

    # Parse the execution report into structured output
    structured_llm = model.with_structured_output(TestExecutionResult)

    prompt_manager = get_prompt_manager()
    parsing_prompt = prompt_manager.render(
        "parse_execution_result.j2",
        scenario_name=scenario.name,
        execution_report=agent_message
    )

    execution_result = cast(TestExecutionResult, structured_llm.invoke(parsing_prompt))
    execution_result.execution_time_seconds = execution_time

    return execution_result


class TestExecutionReport(BaseModel):
    """Report of test scenario execution"""

    total_scenarios: int = Field(description="Total number of scenarios executed")
    passed: int = Field(description="Number of scenarios that passed")
    failed: int = Field(description="Number of scenarios that failed")
    errors: int = Field(description="Number of scenarios with errors")
    results: List[TestExecutionResult] = Field(description="Individual test results")


def downsize_image(img: Image.Image, max_size: tuple[int,int] = (1280,720)) -> Image.Image:
    # Downsize (e.g., to 50% of original size or a specific max width)
    # Using Lanczos for high-quality downsampling
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img

def prepare_screenshot_for_inference(driver: WebDriver) -> str:
    """
    Prepares a browser screenshot for inference by processing and compressing the image data.

    The function captures a screenshot from the provided WebDriver instance, downsizes the image,
    converts it to an appropriate format, and compresses it for efficient storage or transmission.
    The processed image is then encoded into a Base64 string.

    :param driver: WebDriver instance used to capture the screenshot.
    :type driver: WebDriver

    :return: Base64 encoded string representation of the processed screenshot.
    :rtype: str
    """
    screenshot_bytes = driver.get_screenshot_as_png()

    # Open with PIL
    img = Image.open(io.BytesIO(screenshot_bytes))
    img = downsize_image(img)

    # Compress and convert back to bytes
    buffer = io.BytesIO()
    # Convert to RGB if it's RGBA (PNG) to save as JPEG
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Save as JPEG with compression quality 1-95 (85 is a good balance)
    img.save(buffer, format="JPEG", quality=85, optimize=True)

    # Convert to base64 string
    b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"

class UIAssessmentCategory(BaseModel):
    """Assessment of a specific UI category"""
    category: str = Field(description="Category name (e.g., 'Layout', 'Color Scheme', 'Typography')")
    score: int = Field(description="Score from 1-10 for this category")
    feedback: str = Field(description="Detailed feedback about this category")
    issues: Optional[List[str]] = Field(default=None, description="Specific issues identified")


class UIQualityAssessment(BaseModel):
    """Complete UI quality assessment"""
    overall_score: int = Field(description="Overall UI quality score from 1-10")
    overall_feedback: str = Field(description="High-level summary of the UI quality")
    categories: List[UIAssessmentCategory] = Field(description="Detailed assessment by category")
    strengths: List[str] = Field(description="Key strengths of the UI")
    improvements: List[str] = Field(description="Suggested improvements")


def invoke_ui_analyzer_agent(driver: WebDriver,
                             vl_model: BaseChatModel | str = None,
                             model: BaseChatModel | str = None) -> UIQualityAssessment:
    """
    Analyze the UI quality of the current page using a vision-language model.

    This agent captures a screenshot of the current page and uses a VL model to assess
    various aspects of the UI including layout, color scheme, typography, accessibility,
    and user experience.

    Args:
        driver: Selenium WebDriver instance with the page to analyze
        vl_model: Optional vision-language model to use for page analysis
        model: Optional LLM model to use for structured output parsing
    Returns:
        UIQualityAssessment: Structured assessment of the UI quality
    """

    if vl_model is None:
        vl_model = get_vl_model()
    if isinstance(vl_model, str):
        vl_model = init_chat_model(vl_model)

    # Capture the screenshot as bytes
    base64_screenshot = prepare_screenshot_for_inference(driver)

    # Create the analysis prompt
    prompt_manager = get_prompt_manager()
    analysis_prompt = prompt_manager.render("ui_analysis.j2")

    prompt = HumanMessage(
        content=[
            {"type": "text", "text": analysis_prompt},
            {
                "type": "image_url",
                "image_url": {"url": base64_screenshot},
            },
        ]
    )

    # Get the vision model's analysis
    vl_response = vl_model.invoke([prompt])
    analysis_text = vl_response.content if hasattr(vl_response, 'content') else str(vl_response)

    # Parse the unstructured analysis into structured output
    if model is None:
        model = DEFAULT_MODEL
    if isinstance(model, str):
        model = init_chat_model(model)

    structured_llm = model.with_structured_output(UIQualityAssessment)

    prompt_manager = get_prompt_manager()
    parsing_prompt = prompt_manager.render("parse_ui_assessment.j2", analysis_text=analysis_text)

    assessment = cast(UIQualityAssessment, structured_llm.invoke(parsing_prompt))
    return assessment