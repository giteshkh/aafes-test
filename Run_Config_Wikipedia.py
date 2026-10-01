"""
Run_Config_Wikipedia.py
========================
SDK-based suite runner for the Wikipedia sample test.

Mirrors Run_Config_Android.py — reads env vars with sensible defaults so
it works both locally (values from .env file) and in CI (values from
pipeline secrets).

.env support
------------
python-dotenv is loaded at the top so that a .env file at the project root
is automatically picked up before any os.environ reads happen.

Copy env.example to .env and fill in your values, then run:
    python Run_Config_Wikipedia.py

CI: set the same env vars as pipeline secrets and run the same command.
"""

import os
import subprocess

# ── Load .env using absolute path so PyCharm's play button works too ─────────
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass

# ── Read env vars — fall back to sensible defaults for local runs ─────────────
platform_type  = os.getenv("PlatformType",  "android")
device_name    = os.getenv("DeviceName",    "Samsung Galaxy S23")
device_version = os.getenv("DeviceVersion", "13.0")
app_url        = os.getenv("AppURL",        "bs://2cb25d26a5b87168117ec49799f3cc5e51756e61")
session_name   = os.getenv("SESSION_NAME",  "test_wikipedia_sample")
build_name     = os.getenv("BUILD_NAME",    "MEA | Wikipedia | " + platform_type)
build_number   = os.getenv("BUILD_NUMBER",  "1")

# ── Propagate to child processes (SDK reads these at runtime) ─────────────────
os.environ["PlatformType"]  = platform_type
os.environ["DeviceName"]    = device_name
os.environ["DeviceVersion"] = device_version
os.environ["AppURL"]        = app_url
os.environ["SESSION_NAME"]  = session_name
os.environ["BUILD_NAME"]    = build_name
os.environ["BUILD_NUMBER"]  = build_number

# BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY are already in os.environ
# (loaded from .env above or set by CI) — the SDK reads them automatically.

# Tell the SDK which config file to use
os.environ["BROWSERSTACK_CONFIG_FILE"] = "browserstack_wikipedia.yml"

# ── Run the Wikipedia sample test via the BrowserStack SDK ───────────────────
command = (
    "browserstack-sdk pytest "
    "--config browserstack_wikipedia.yml "
    "smoke/test_wikipedia_sample.py "
    "--alluredir=allure-results"
)

print(f"Running: {command}")
subprocess.run(command, shell=True)