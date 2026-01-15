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
    system_message = """You are a web testing expert specializing in creating comprehensive test scenarios.

You have access to Selenium browser tools to navigate and interact with web pages. Your task is to:
1. Use the selenium_navigate tool to visit the requested URL
2. Use selenium_get_page_text or selenium_get_page_content to extract page information
3. Analyze the page structure, content, and interactive elements
4. Generate simple test scenarios covering (some, not necessarily all):
   - User navigation flows
   - Form submissions and validations
   - Interactive elements (buttons, links, dropdowns)
   - Accessibility features
5. Test scenarios should be focused on a single task and should be VERY simple
6. Generate up to 3 test scenarios.
7. IGNORE content not relevant to testing


Format your test scenarios clearly with:
- Scenario name/title
- Objective (what is being tested)
- Steps (user actions)
- Expected results
- Preconditions (if any)

Be thorough and consider edge cases, error conditions, and user experience aspects."""

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

    parsing_prompt = f"""Parse the following test scenarios into structured format.
Extract each scenario's name, objective, steps (as a list), expected result, and preconditions.

Test Scenarios:
{scenario_text}

Return a structured list of all scenarios found in the text."""

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
    system_message = """You are an automated test execution agent. Your task is to:
1. Execute test scenarios step by step using Selenium browser tools
2. Verify that each step produces the expected outcome
3. Report any failures or errors encountered
4. Determine if the test PASSED or FAILED based on the expected results

Guidelines:
- Keep test scenarios VERY SIMPLE and focused on a single task
- The scenario should only be executed once
- Execute each step in the test scenario sequentially
- Focus mainly on final results
- If any step fails, mark the test as FAILED and explain why
- If all steps complete and match expected results, mark as PASSED
- If you encounter technical errors (element not found, timeout, etc.), mark as ERROR
"""

    # Create the execution prompt
    steps_text = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(scenario.steps)])

    execution_prompt = f"""Execute the following test scenario:

**Scenario Name**: {scenario.name}
**Objective**: {scenario.objective}
**Preconditions**: {scenario.preconditions or 'None'}
**Base URL**: {url}

**Steps to Execute**:
{steps_text}

**Expected Result**: {scenario.expected_result}

Execute each step carefully using the available Selenium tools. After completing all steps, evaluate whether the actual results match the expected results. Provide a detailed report of what happened during execution."""

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

    parsing_prompt = f"""Based on the following test execution report, create a structured test result.

Scenario Name: {scenario.name}

Execution Report:
{agent_message}

Analyze the report and determine:
- status: "PASSED" if all steps completed successfully and expected results were met, "FAILED" if expected results were not met, "ERROR" if technical issues prevented execution
- execution_details: Summary of what happened during execution
- errors_encountered: List of any errors or failures (empty list if none)

Return the structured test execution result."""

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
    analysis_prompt = """Analyze this web page UI and provide a comprehensive quality assessment. Evaluate the following aspects:

1. **Layout & Structure**: Is the layout well-organized, balanced, and intuitive? Are elements properly aligned?
2. **Color Scheme**: Is the color palette harmonious and appropriate? Does it provide good contrast and readability?
3. **Typography**: Are fonts readable, appropriately sized, and consistently used?
4. **Visual Hierarchy**: Is it clear what's important? Do headings, buttons, and content have proper emphasis?
5. **Whitespace & Density**: Is there adequate spacing between elements? Is the page too cluttered or too sparse?
6. **Consistency**: Are UI elements, styles, and patterns used consistently throughout?
7. **Accessibility**: Does the design appear accessible (contrast, text size, clear interactive elements)?
8. **Modern Design**: Does it follow current UI/UX best practices?

Provide a detailed analysis covering strengths, weaknesses, and specific recommendations for improvement."""

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

    parsing_prompt = f"""Based on the following UI analysis, create a structured quality assessment.

UI Analysis:
{analysis_text}

Extract and structure:
- An overall quality score (1-10)
- Overall feedback summary
- Category-based assessments (Layout, Color Scheme, Typography, Visual Hierarchy, Accessibility, etc.)
  Each category should have a score (1-10), feedback, and specific issues if any
- List of key strengths
- List of suggested improvements

Return the structured UI quality assessment."""

    assessment = cast(UIQualityAssessment, structured_llm.invoke(parsing_prompt))
    return assessment