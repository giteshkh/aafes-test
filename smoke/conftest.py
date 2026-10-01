"""
smoke/conftest.py
-----------------
Minimal conftest for the Wikipedia sample test.

Used when running the test standalone (no SDK, no customer internal modules):
    pytest smoke/test_wikipedia_sample.py

For SDK runs, the root conftest.py manages the driver instead.

.env loading: python-dotenv is loaded here so that running pytest directly
from the smoke/ directory also picks up the .env file at the project root.
"""

import os
import sys
import pytest
from appium import webdriver
from appium.options.common.base import AppiumOptions

# ── Ensure project root is on sys.path so Initializer can be imported ────────
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ── Load .env from project root (absolute path — CWD-independent) ────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(_project_root, ".env"), override=False)
except ImportError:
    pass


def _create_driver():
    username   = os.environ.get("BROWSERSTACK_USERNAME", "")
    access_key = os.environ.get("BROWSERSTACK_ACCESS_KEY", "")
    app_url    = os.environ.get("AppURL", "bs://2cb25d26a5b87168117ec49799f3cc5e51756e61")
    device     = os.environ.get("DeviceName", "Samsung Galaxy S23")
    version    = os.environ.get("DeviceVersion", "13.0")
    platform   = os.environ.get("PlatformType", "android")
    session    = os.environ.get("SESSION_NAME", "test_wikipedia_sample")
    build      = os.environ.get("BUILD_NAME", "MEA | Wikipedia | android")
    build_num  = os.environ.get("BUILD_NUMBER", "1")

    if not username or not access_key:
        raise EnvironmentError(
            "BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY must be set. "
            "Copy env.example to .env and fill in your credentials."
        )

    hub_url = f"https://{username}:{access_key}@hub-cloud.browserstack.com/wd/hub"

    options = AppiumOptions()
    options.load_capabilities({
        "platformName": platform,
        "deviceName": device,
        "platformVersion": version,
        "appium:automationName": "UiAutomator2",
        "appium:app": app_url,
        "appium:noReset": "true",
        "appium:newCommandTimeout": 400,
        "bstack:options": {
            "projectName": "AAFES-MEA",
            "buildName": build,
            "sessionName": session,
            "buildIdentifier": build_num,
            "debug": True,
            "proxyUnawareApp": True,
        },
    })

    return webdriver.Remote(hub_url, options=options)


@pytest.fixture(scope="function", autouse=True)
def driver_setup_and_teardown(request):
    """
    Create a BrowserStack Appium session and attach it to request.node.driver
    so test methods can access it via `request.node.driver`.
    """
    driver = _create_driver()
    request.node.driver = driver
    yield
    try:
        driver.quit()
    except Exception as e:
        print(f"[teardown] Error quitting driver: {e}")