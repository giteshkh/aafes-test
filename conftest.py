import os
import time
import yaml
import pytest
from appium import webdriver
from appium.options.common.base import AppiumOptions
from Initializer import Initializer
from browserstack_api.app_profiling_api import BrowserStackApi
from dbconnector.mysql_connector import MetricsParser
from tests.platformTypeMode import PlatformType

from selenium.common.exceptions import WebDriverException


def pytest_addoption(parser):
    parser.addoption(
        "--config",
        action="store",
        default="browserstack_android.yml",
        help="Path to the BrowserStack YAML configuration file"
    )


# @pytest.fixture(scope='function', autouse=True)
# def driver_setup_and_teardown(request):
#
#     if hasattr(request.node, 'driver') and request.node.driver:
#         print("Driver already exists, skipping creation.")
#         yield
#         return
#
#     config_file = request.config.getoption("--config")
#     config = load_browserstack_config(config_file)
#     device_index = 0  # Adjust this index as needed for different devices
#
#     # Create the Appium driver using the configuration
#     driver = create_driver_from_config(config, device_index)
#
#     # Store the driver instance in the request context
#     request.node.driver = driver
#
#     # Yield control back to the test
#     yield
#
#     # Teardown: Quit the driver after each test
#     if hasattr(request.node, 'driver'):
#         request.node.driver.quit()
#         print("Driver quit after test execution")
#
#     # Perform any additional cleanup
#     # Pass the test method name directly to cleanup_method
#     cleanup_method(request.node.name)

@pytest.fixture(scope='function', autouse=True)
def driver_setup_and_teardown(request):

    if hasattr(request.node, 'driver') and request.node.driver:
        print("Driver already exists, skipping creation.")
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
        # log but don't fail test if quit() explodes
        print(f"[teardown] Error while quitting driver for {request.node.name}: {e}")

    # DB / profiling / metrics cleanup should never break the test
    try:
        cleanup_method(request.node.name)
    except Exception as e:
        # this is where your JSON/DB error was propagating from
        print(f"[teardown] Cleanup failed for {request.node.name}: {e}")
        # do NOT re-raise, otherwise pytest marks it as teardown ERROR[web:22][web:28]


def load_browserstack_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    # Without the SDK the yml's ${VAR} placeholders are not substituted; resolve them from
    # the environment so the legacy (no-SDK) path sees real values. No-op when the SDK ran.
    return _resolve_env_placeholders(config)


def _resolve_env_placeholders(value):
    if isinstance(value, dict):
        return {k: _resolve_env_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_placeholders(v) for v in value]
    if isinstance(value, str):
        return os.path.expandvars(value)
    return value


def create_driver_from_config(config, device_index):
    device_config = config['platforms'][device_index]  # Assumes 'platforms' is a list of device configs
    if PlatformType == 'iOS':
        automation_name = "XCUITest"
    else:
        automation_name = "UiAutomator2"
    options = AppiumOptions()
    capabilities = {
        "platformName": device_config.get("platformName"),
        "platformVersion": device_config.get("platformVersion"),
        "deviceName": device_config.get("deviceName"),
        "appium:automationName": automation_name, #for ios 'XCUITest' and for android 'UiAutomator2'
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
        "appProfiling": config.get("appProfiling", True)
    }

    # Add BrowserStack options if they are specified
    if bstack_options:
        capabilities["bstack:options"] = bstack_options

    options.load_capabilities(capabilities)

    # Without the SDK the yml's ${VAR} placeholders are never substituted, so fall back to the
    # environment variables (credentials stay out of the code and the yml).
    user_name = config['userName']
    access_key = config['accessKey']
    if str(user_name).startswith("${"):
        user_name = os.environ.get("BROWSERSTACK_USERNAME", user_name)
    if str(access_key).startswith("${"):
        access_key = os.environ.get("BROWSERSTACK_ACCESS_KEY", access_key)
    hub_url = f"https://{user_name}:{access_key}@hub-cloud.browserstack.com/wd/hub"
    driver_instance = webdriver.Remote(hub_url, options=options)

    Initializer.SESSION_ID = driver_instance.session_id
    print(f"Driver created with session ID: {Initializer.SESSION_ID}")

    return driver_instance


# def cleanup_method(test_method_name):
#     time.sleep(12)  # Wait for 10 seconds
#     session_id = Initializer.SESSION_ID
#     print(f"Session ID: {session_id}")
#     print(f"Test Method Name: {test_method_name}")
#     # save_ids_to_file(test_method_name, "Just like that")
#     # Retrieve and save the build ID and profiling data
#     build_id = BrowserStackApi.get_running_build_id()
#     build_name = BrowserStackApi.get_running_build_name()
#     # save_ids_to_file(build_name, build_id)
#     build_info = {
#         "build_name": build_name,
#         "build_id": build_id,
#         "session_id": session_id
#     }
#
#     profiling_data = BrowserStackApi.get_profiling_data(build_id, session_id)
#     # BrowserStackApi.save_data_to_file(profiling_data, "profiling_data_1.json")
#     MetricsParser.update_database(profiling_data, build_info, test_method_name, "com.aafes.shopmyexchange.qa")
#     print("Cleanup complete")

def cleanup_method(test_method_name):
    time.sleep(12)  # Wait for BrowserStack to finalize profiling

    session_id = Initializer.SESSION_ID
    print(f"Session ID: {session_id}")
    print(f"Test Method Name: {test_method_name}")

    # Get build info from BrowserStack
    build_id = BrowserStackApi.get_running_build_id()
    build_name = BrowserStackApi.get_running_build_name()

    if not build_id or not build_name:
        print(f"[cleanup] No running build found for {test_method_name}, skipping DB update")
        return

    build_info = {
        "build_name": build_name,
        "build_id": build_id,
        "session_id": session_id
    }

    # Get profiling data; this can be None or empty
    profiling_data = BrowserStackApi.get_profiling_data(build_id, session_id)

    if not profiling_data:
        print(f"[cleanup] No profiling data for build {build_id}, session {session_id}, skipping DB update")
        return

    # Wrap DB update so any JSON/DB issues do not fail teardown
    try:
        MetricsParser.update_database(
            profiling_data,
            build_info,
            test_method_name,
            "com.aafes.shopmyexchange.qa"
        )
        print("Cleanup complete")
    except Exception as e:
        # Log and swallow – do NOT re-raise, otherwise pytest marks test as ERROR
        print(f"[cleanup] Metrics update failed for {test_method_name}: {e}")


def save_ids_to_file(session_id, build_id, filename='ids.txt'):
    with open(filename, 'w') as file:
        file.write(f"Session ID: {session_id}\n")
        file.write(f"Build ID: {build_id}\n")
    print(f"IDs saved to {filename}")

import pytest
from selenium.common.exceptions import WebDriverException

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """
    Framework-level hook to normalize unexpected Selenium exceptions so Allure
    treats them as FAILED instead of BROKEN.
    """
    outcome = yield  # run the test body

    excinfo = outcome.excinfo  # None or (exc_type, exc_value, traceback)

    if excinfo is None:
        # Test passed (no exception)
        return

    exc_type, exc_value, _ = excinfo

    # Already an assertion-style failure -> leave as is
    if issubclass(exc_type, AssertionError):
        return

    # Only convert Selenium/WebDriver exceptions; other exceptions remain Broken
    if issubclass(exc_type, WebDriverException):
        pytest.fail(
            f"Selenium error normalized as failure: {exc_type.__name__}: {exc_value}",
            pytrace=True,
        )

if __name__ == "__main__":
    # Example usage of cleanup_method (not typically used in conftest.py)
    cleanup_method("example_test_method")
