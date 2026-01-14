from typing import List, Optional, cast

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from selenium.webdriver.remote.webdriver import WebDriver
from .prompt_manager import get_prompt_manager
import time

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
