from selenium import webdriver

import config


def create_headless_firefox_driver():
    """Create a headless Firefox WebDriver with typing."""
    from selenium.webdriver.firefox.options import Options
    from webdriver_manager.firefox import GeckoDriverManager
    from selenium.webdriver.firefox.service import Service

    options = Options()
    options.add_argument(f"--width={config.config.browser_width}")  # ensures proper page layout
    options.add_argument(f"--height={config.config.browser_height}")
    if config.config.headless_browser:
        options.add_argument("--headless")

    driver = webdriver.Firefox(options=options, service=Service(GeckoDriverManager().install()))
    return driver


def create_selenium_driver():
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service

    options = Options()
    # options.add_argument("--headless=new")  # modern headless
    # options.add_argument("--disable-gpu")  # often recommended
    # options.add_argument("--window-size=1920,1080")  # ensures proper page layout
    # options.add_argument("--no-sandbox")  # useful in Linux CI
    # options.add_argument("--disable-dev-shm-usage")  # avoid memory issues
    driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
    return driver
