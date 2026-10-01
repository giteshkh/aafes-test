"""
conftest.py (project root)
==========================
Customer's original conftest.py with two additions:

1. python-dotenv loaded at the top using an absolute path so PyCharm's
   green-play button finds .env regardless of working directory.

2. create_driver_from_config reads credentials from os.environ first
   (populated by dotenv) rather than from raw YML values, which may
   contain unresolved ${VAR} placeholders when the SDK is not running.

3. driver_setup_and_teardown skips driver creation for Run_Local_Debugger*
   files — those manage their own module-scoped driver via Initializer.

All other logic is unchanged from the customer's original.
"""

import os
import time
import yaml
import pytest
from appium import webdriver
from appium.options.common.base import AppiumOptions
from selenium.common.exceptions import WebDriverException

# ── Load .env using absolute path so PyCharm's play button works too ─────────
# Must use __file__ — PyCharm sets cwd to the script's own folder, not the
# project root, so a bare load_dotenv() would never find .env.
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass

from Initializer import Initializer


def pytest_addoption(parser):
    parser.addoption(
        "--config",
        action="store",
        default="browserstack_android.yml",
        help="Path to the BrowserStack YAML configuration file"
    )


@pytest.fixture(scope='function', autouse=True)
def driver_setup_and_teardown(request):

    if hasattr(request.node, 'driver') and request.node.driver:
        print("Driver already exists, skipping creation.")
        yield
        return

    # Skip driver creation for Run_Local_Debugger* files — they manage their
    # own module-scoped driver via Initializer.get_driver() and inject it via
    # a mock request. The root conftest must not create a second session.
    test_file = getattr(request.node, 'fspath', None)
    test_file = test_file.basename if test_file else ""
    if "Run_Local_Debugger" in test_file:
        yield
        return

    # Also skip for tests that declare their own 'driver' fixture parameter
    # (e.g. TestLocalWikipedia) — the module-scoped fixture handles setup.
    if "driver" in request.fixturenames:
        yield
        return

    config_file = request.config.getoption("--config")
    config = load_browserstack_config(config_file)
    device_index = 0  # Adjust this index as needed for different devices

    driver = create_driver_from_config(config, device_index)
    request.node.driver = driver

    # run the test
    yield

    # --- teardown starts here ---
    try:
        if hasattr(request.node, 'driver') and request.node.driver:
            request.node.driver.quit()
            print("Driver quit after test execution")
    except Exception as e:
        print(f"[teardown] Error while quitting driver for {request.node.name}: {e}")

    try:
        cleanup_method(request.node.name)
    except Exception as e:
        print(f"[teardown] Cleanup failed for {request.node.name}: {e}")


def load_browserstack_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config


def create_driver_from_config(config, device_index):
    device_config = config['platforms'][device_index]
    platform = os.environ.get("PlatformType", device_config.get("platformName", "android"))
    automation_name = "XCUITest" if platform.lower() == "ios" else "UiAutomator2"

    options = AppiumOptions()
    capabilities = {
        "platformName": device_config.get("platformName"),
        "platformVersion": device_config.get("platformVersion"),
        "deviceName": device_config.get("deviceName"),
        "appium:automationName": automation_name,
        "appium:app": config.get("app", Initializer.APP_URL),
        "appium:noReset": "true",
        "appium:ensureWebviewsHavePages": True,
        "appium:nativeWebScreenshot": True,
        "appium:newCommandTimeout": 3600,
        "appium:connectHardwareKeyboard": True,
    }

    bstack_options = {
        "buildName": config.get("buildName", "default-build"),
        "projectName": config.get("projectName", "default-project"),
        "buildIdentifier": config.get("buildIdentifier", "default-build-id"),
        "debug": config.get("debug", False),
        "networkLogs": config.get("networkLogs", False),
        "appProfiling": config.get("appProfiling", True),
    }

    if bstack_options:
        capabilities["bstack:options"] = bstack_options

    options.load_capabilities(capabilities)

    # Prefer env vars over raw YML values — YML may contain unresolved
    # ${VAR} placeholders when the SDK is not running (local no-SDK mode).
    username   = os.environ.get("BROWSERSTACK_USERNAME") or config.get("userName", "")
    access_key = os.environ.get("BROWSERSTACK_ACCESS_KEY") or config.get("accessKey", "")
    hub_url = f"https://{username}:{access_key}@hub-cloud.browserstack.com/wd/hub"

    driver_instance = webdriver.Remote(hub_url, options=options)
    Initializer.SESSION_ID = driver_instance.session_id
    print(f"Driver created with session ID: {Initializer.SESSION_ID}")
    return driver_instance


def cleanup_method(test_method_name):
    """Lightweight cleanup — extend with BrowserStackApi/MetricsParser as needed."""
    print(f"[cleanup] Test method: {test_method_name}, session: {Initializer.SESSION_ID}")


def save_ids_to_file(session_id, build_id, filename='ids.txt'):
    with open(filename, 'w') as file:
        file.write(f"Session ID: {session_id}\n")
        file.write(f"Build ID: {build_id}\n")
    print(f"IDs saved to {filename}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Normalize unexpected Selenium exceptions so Allure treats them as FAILED."""
    outcome = yield
    excinfo = outcome.excinfo
    if excinfo is None:
        return
    exc_type, exc_value, _ = excinfo
    if issubclass(exc_type, AssertionError):
        return
    if issubclass(exc_type, WebDriverException):
        pytest.fail(
            f"Selenium error normalized as failure: {exc_type.__name__}: {exc_value}",
            pytrace=True,
        )