"""
Run_Config_Android.py
=====================
Customer's original SDK-based suite runner.

.env support added: python-dotenv is loaded at the top using an absolute
path so PyCharm's green-play button finds .env regardless of cwd.

Usage (local — after filling in .env):
    python Run_Config_Android.py

CI: set the same env vars as pipeline secrets and run the same command.
"""

import os
import subprocess
from datetime import datetime

# ── Load .env using absolute path so PyCharm's play button works too ─────────
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass


def get_project_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    return project_root


project_root = get_project_root()
print(project_root)

suite_name      = os.getenv("SuiteName",      "Smoke")
platform_type   = os.getenv("PlatformType",   "android")
automation_name = os.getenv("AutomationName", "UiAutomator2")
app_url         = os.getenv("AppURL",         "bs://YOUR_APP_URL_HERE")
device_name     = os.getenv("DeviceName",     "Samsung Galaxy S23")
device_version  = os.getenv("DeviceVersion",  "13.0")

# Propagate to child processes (SDK reads these at runtime)
os.environ["SuiteName"]      = suite_name
os.environ["PlatformType"]   = platform_type
os.environ["AutomationName"] = automation_name
os.environ["AppURL"]         = app_url
os.environ["DeviceName"]     = device_name
os.environ["DeviceVersion"]  = device_version

os.environ['PYTHONPATH'] = project_root + os.pathsep + os.getenv('PYTHONPATH', '')
os.environ['BROWSERSTACK_CONFIG_FILE'] = 'browserstack_android.yml'

# Run Smoke
if suite_name == "Smoke":
    test_classes = ["test_keepmesignedin"]
    current_date = datetime.now().strftime("%Y%m%d")
    for test_class in test_classes:
        os.environ["SESSION_NAME"] = test_class
        os.environ["BUILD_NAME"] = "MEA | Smoke | " + platform_type
        command = (
            f'browserstack-sdk pytest '
            f'--config browserstack_android.yml '
            f'smoke/{test_class}.py '
            f'--alluredir=allure-results'
        )
        subprocess.run(command, shell=True)