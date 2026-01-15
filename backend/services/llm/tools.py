"""
LLM Tools for Selenium Web Browsing using Langchain
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from bs4 import BeautifulSoup


# Global browser manager instance


def sanitize_text(text: str, is_html: bool = False, max_length: int = 1000) -> str:
    """
    Sanitize text/HTML by removing unreadable characters, reducing HTML boilerplate, and truncating.

    Args:
        text: The text or HTML to sanitize
        is_html: Whether the input is HTML (enables HTML-specific processing)
        max_length: Maximum length of the returned string

    Returns:
        Sanitized and truncated text
    """
    if not text:
        return text

    # If HTML, parse and extract meaningful content
    if is_html:
        try:
            soup = BeautifulSoup(text, 'html.parser')

            # Remove script and style elements
            for element in soup(['script', 'style', 'meta', 'link', 'noscript', 'header', 'footer', 'nav']):
                element.decompose()

            # Get text content
            text = soup.get_text(separator=' ', strip=True)
        except:
            pass  # Fall back to text processing

    # Remove control characters and non-printable characters
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Normalize whitespace (replace multiple spaces/newlines with single space)
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


# Structured Output Models


# Tool Input Schemas
class NavigateInput(BaseModel):
    url: str = Field(description="The URL to navigate to")


class GetPageContentInput(BaseModel):
    pass


class FindElementInput(BaseModel):
    selector: str = Field(description="CSS selector to find the element")
    timeout: int = Field(default=10, description="Timeout in seconds to wait for element")


class ClickElementInput(BaseModel):
    selector: str = Field(description="CSS selector of the element to click")
    timeout: int = Field(default=10, description="Timeout in seconds to wait for element")


class InputTextInput(BaseModel):
    selector: str = Field(description="CSS selector of the input field")
    text: str = Field(description="Text to input into the field")
    timeout: int = Field(default=10, description="Timeout in seconds to wait for element")


class GetElementTextInput(BaseModel):
    selector: str = Field(description="CSS selector of the element")
    timeout: int = Field(default=10, description="Timeout in seconds to wait for element")


class ExecuteScriptInput(BaseModel):
    script: str = Field(description="JavaScript code to execute")


class WithSeleniumDriver(BaseTool):
    """
    Represents a tool that utilizes a Selenium WebDriver.

    This class serves as an interface for interacting with a Selenium WebDriver
    to automate browser activities. It inherits from the `BaseTool` class and
    is initialized with a Selenium WebDriver instance. This class is designed
    to facilitate browser-related functionalities by managing a WebDriver instance.
    """
    _driver: WebDriver = PrivateAttr()

    def __init__(self, driver: WebDriver, **kwargs):
        super().__init__(**kwargs)
        self._driver = driver


# Selenium Tools
class SeleniumNavigateTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_navigate",
            description="Navigate to a URL using Selenium browser. Use this to visit web pages.",
            args_schema=NavigateInput,
        )

    def _run(self, url: str) -> str:
        try:
            self._driver.get(url)
            return f"Successfully navigated to {url}. Page title: {self._driver.title}"
        except Exception as e:
            return f"Error navigating to {url}: {str(e)}"


class SeleniumGetPageContentTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_get_page_content",
            description="Get the full HTML content of the current page. Use this to extract page structure and content.",
            args_schema=GetPageContentInput,
        )

    def _run(self) -> str:
        try:
            return sanitize_text(self._driver.page_source, is_html=True)
        except Exception as e:
            return f"Error getting page content: {str(e)}"


class SeleniumGetPageTextTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_get_page_text",
            description="Get the visible text content of the current page. Use this to read what's displayed on the page.",
            args_schema=GetPageContentInput,
        )

    def _run(self) -> str:
        try:
            text = self._driver.find_element(By.TAG_NAME, "body").text
            return sanitize_text(text)
        except Exception as e:
            return f"Error getting page text: {str(e)}"


class SeleniumFindElementTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_find_element",
            description="Find an element on the page using a CSS selector. Returns whether the element exists and its basic info.",
            args_schema=FindElementInput,
        )

    def _run(self, selector: str, timeout: int = 10) -> str:
        try:
            wait = WebDriverWait(self._driver, timeout)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            sanitized_text = sanitize_text(element.text, max_length=100)
            return f"Element found: {element.tag_name}, text: {sanitized_text}, visible: {element.is_displayed()}"
        except TimeoutException:
            return f"Element with selector '{selector}' not found within {timeout} seconds"
        except Exception as e:
            return f"Error finding element: {str(e)}"


class SeleniumClickElementTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_click_element",
            description="Click an element on the page using a CSS selector. Use this to interact with buttons, links, etc.",
            args_schema=ClickElementInput,
        )

    def _run(self, selector: str, timeout: int = 10) -> str:
        try:
            wait = WebDriverWait(self._driver, timeout)
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            element.click()
            return f"Successfully clicked element with selector '{selector}'"
        except TimeoutException:
            return f"Element with selector '{selector}' not clickable within {timeout} seconds"
        except Exception as e:
            return f"Error clicking element: {str(e)}"


class SeleniumInputTextTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_input_text",
            description="Input text into a field on the page using a CSS selector. Use this to fill forms.",
            args_schema=InputTextInput,
        )

    def _run(self, selector: str, text: str, timeout: int = 10) -> str:
        try:
            wait = WebDriverWait(self._driver, timeout)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            element.clear()
            element.send_keys(text)
            return f"Successfully input text into element with selector '{selector}'"
        except TimeoutException:
            return f"Element with selector '{selector}' not found within {timeout} seconds"
        except Exception as e:
            return f"Error inputting text: {str(e)}"


class SeleniumGetElementTextTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_get_element_text",
            description="Get the text content of a specific element using a CSS selector.",
            args_schema=GetElementTextInput,
        )

    def _run(self, selector: str, timeout: int = 10) -> str:
        try:
            wait = WebDriverWait(self._driver, timeout)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return sanitize_text(element.text)
        except TimeoutException:
            return f"Element with selector '{selector}' not found within {timeout} seconds"
        except Exception as e:
            return f"Error getting element text: {str(e)}"


class SeleniumExecuteScriptTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_execute_script",
            description="Execute JavaScript code on the current page. Use this for advanced interactions or data extraction.",
            args_schema=ExecuteScriptInput,
        )

    def _run(self, script: str) -> str:
        try:
            result = self._driver.execute_script(script)
            if result is not None:
                result_str = str(result)
                return sanitize_text(result_str)
            return "Script executed successfully"
        except Exception as e:
            return f"Error executing script: {str(e)}"


class SeleniumGetCurrentUrlTool(WithSeleniumDriver):
    def __init__(self, driver: WebDriver):
        super().__init__(
            driver=driver,
            name="selenium_get_current_url",
            description="Get the current URL of the browser.",
            args_schema=GetPageContentInput,
        )

    def _run(self) -> str:
        try:
            return self._driver.current_url
        except Exception as e:
            return f"Error getting current URL: {str(e)}"


# Collection of all Selenium tools
def get_selenium_tools(driver: WebDriver):
    """Get all available Selenium browsing tools"""
    return [
        SeleniumNavigateTool(driver=driver),
        SeleniumGetPageContentTool(driver=driver),
        SeleniumGetPageTextTool(driver=driver),
        SeleniumFindElementTool(driver=driver),
        SeleniumClickElementTool(driver=driver),
        SeleniumInputTextTool(driver=driver),
        SeleniumGetElementTextTool(driver=driver),
        SeleniumExecuteScriptTool(driver=driver),
        SeleniumGetCurrentUrlTool(driver=driver),
    ]
