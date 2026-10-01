"""
Initializer.py
==============
Mirrors the customer's Initializer.py with one addition:
python-dotenv is loaded at import time so that a local .env file
(copied from env.example) is automatically picked up in all run modes —
including when PyCharm's green-play button runs the file directly.

Priority order for every value:
  1. Real environment variable (CI pipeline / shell export)
  2. .env file in the project root (local development)
  3. Hard-coded fallback below (last resort)

Key fix for PyCharm: load_dotenv() uses an absolute path derived from
__file__ so it works regardless of what PyCharm sets as the working
directory. It runs BEFORE the class body so that USERNAME, ACCESS_KEY,
APP_URL, and HUB_URL are all set from .env at class-definition time.
"""

import os
import datetime
import requests
from appium import webdriver
from appium.options.common.base import AppiumOptions

# ── Load .env BEFORE the class body reads os.environ ─────────────────────────
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass  # python-dotenv not installed — env vars must be set another way


class Initializer:
    USERNAME   = os.environ.get("BROWSERSTACK_USERNAME", "your_username_here")
    ACCESS_KEY = os.environ.get("BROWSERSTACK_ACCESS_KEY", "your_access_key_here")
    APP_URL    = os.environ.get("AppURL", "bs://2cb25d26a5b87168117ec49799f3cc5e51756e61")

    HUB_URL = (
        f"https://{os.environ.get('BROWSERSTACK_USERNAME', 'your_username_here')}"
        f":{os.environ.get('BROWSERSTACK_ACCESS_KEY', 'your_access_key_here')}"
        f"@hub-cloud.browserstack.com/wd/hub"
    )

    BUILD_ID   = ""
    SESSION_ID = ""

    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    @classmethod
    def get_driver(cls, device_index):
        devices = [
            {"platformVersion": "14.0", "deviceName": "Google Pixel 8 Pro"},
            {"platformVersion": "12.0", "deviceName": "Samsung Galaxy S22 Ultra"},
            {"platformVersion": "13.0", "deviceName": "OnePlus 11R"},
            {"platformVersion": "14.0", "deviceName": "Google Pixel 8"},
            {"platformVersion": "13.0", "deviceName": "Samsung Galaxy S23 Ultra"},
            {"platformVersion": "14.0", "deviceName": "Samsung Galaxy S24 Ultra"},
            {"platformVersion": "11.0", "deviceName": "Samsung Galaxy S21 Ultra"},
            {"platformVersion": "12.0", "deviceName": "Google Pixel 6 Pro"},
            {"platformVersion": "10.0", "deviceName": "Google Pixel 4 XL"},
            {"platformVersion": "11.0", "deviceName": "OnePlus 9"},
            {"platformVersion": "10.0", "deviceName": "OnePlus 8"},
            {"platformVersion": "17.0", "deviceName": "iPhone 15"},
        ]

        device = devices[device_index]

        # Build/session metadata — env vars win; sensible defaults ensure
        # BrowserStack always shows a meaningful name even when .env isn't loaded.
        _ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        # Append timestamp to buildName so each run creates a NEW build on the
        # BrowserStack dashboard instead of appending as "Re-run N".
        _base_name   = os.environ.get("BUILD_NAME",   "MEA | Local Debug")
        build_name   = f"{_base_name} | {_ts}"
        session_name = os.environ.get("SESSION_NAME", "test_wikipedia_local")
        project_name = os.environ.get("ProjectName",  "AAFES-MEA")

        options = AppiumOptions()
        options.load_capabilities({
            "platformName": "android",
            "platformVersion": device["platformVersion"],
            "deviceName": device["deviceName"],
            "appium:automationName": "UiAutomator2",
            "appium:app": cls.APP_URL,
            "appium:noReset": "true",
            "appium:ensureWebviewsHavePages": True,
            "appium:nativeWebScreenshot": True,
            "bstack:options": {
                "source": "appiumdesktop",
                "aiAuthoring": True,
                "projectName":    project_name,
                "buildName":      build_name,
                "sessionName":    session_name,
                # proxyUnawareApp: tells BrowserStack the app does not go through
                # the BrowserStack proxy — required for apps that handle their own
                # network stack and break when proxied.
                "proxyUnawareApp": True,
            },
            "browserstack.idleTimeout": "300",
            "appium:newCommandTimeout": 3600,
            "appium:connectHardwareKeyboard": True,
            "browserstack.video": "true",
            "appProfiling": True,
        })

        driver_instance = webdriver.Remote(cls.HUB_URL, options=options)
        Initializer.SESSION_ID = driver_instance.session_id
        return driver_instance

    @classmethod
    def update_session_status(cls, session_id, status, reason):
        url = f"https://api.browserstack.com/automate/sessions/{session_id}.json"
        headers = {"Content-Type": "application/json"}
        payload = {"status": status, "reason": reason}
        response = requests.put(
            url, headers=headers, json=payload,
            auth=(cls.USERNAME, cls.ACCESS_KEY)
        )
        if response.status_code == 200:
            print(f"Session status updated successfully: {url}")
        else:
            print(f"Failed to update session status: {response.status_code}")
            print(response.json())

    @classmethod
    def get_session_url(cls, session_id):
        return (
            f"Dashboard: https://app-automate.browserstack.com"
            f"/dashboard/v2/sessions/{session_id}"
        )