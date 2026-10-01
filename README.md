# AAFES MEA — BrowserStack App Automate Sample Repo

This repo is a minimal, self-contained reference for the AAFES MEA test suite.
It contains a Wikipedia sample test (verified working, no login required) to validate the infrastructure, and the customer's login test ready to run against the AAFES app.

---

## 1. Prerequisites

- Python 3.9+
- BrowserStack App Automate account

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 2. One-time setup

Copy `env.example` to `.env` and fill in your values:

```bash
cp env.example .env
```

Edit `.env`:

```
BROWSERSTACK_USERNAME=your_browserstack_username
BROWSERSTACK_ACCESS_KEY=your_browserstack_access_key

# Wikipedia sample (apk file included):
AppURL=bs://YOUR_WIKIPEDIA_APP_URL_HERE

# Customer AAFES MEA app — replace with your uploaded bs:// URL:
# AppURL=bs://YOUR_AAFES_APP_URL_HERE

PlatformType=android
DeviceName=Samsung Galaxy S23
DeviceVersion=13.0

SESSION_NAME=test_keepmesignedin
BUILD_NAME=MEA | Smoke | android

# AAFES app credentials
APP_USERNAME=automlplus01
APP_PASSWORD=Aafes123#
```

Upload your APK to BrowserStack once:

```bash
curl -u "USERNAME:ACCESS_KEY" \
  -X POST "https://api-cloud.browserstack.com/app-automate/upload" \
  -F "file=@/path/to/your/app.apk"
# Returns: { "app_url": "bs://abc123..." }
# Set AppURL=bs://abc123... in .env
```

---

## 3. The proxyUnawareApp capability

The AAFES app handles its own network stack and breaks when BrowserStack routes traffic through its internal proxy. The `proxyUnawareApp: true` capability tells BrowserStack to bypass its proxy for this app.

It is set in **all three run modes**:

| Mode | Where it is set |
|---|---|
| No-SDK (Initializer.py) | `bstack:options` inside `get_driver()` |
| SDK local / CI | `browserstack_android.yml` — `proxyUnawareApp: true` |
| Standalone pytest | `smoke/conftest.py` — `bstack:options` |

**Verified on BrowserStack dashboard** — the capability shows as `browserstack.proxyUnawareApp: true` in the session input caps.

**Root cause of the original error:** When `${AppURL}` env var was not exported before running `browserstack-sdk pytest`, the SDK could not resolve the app URL and fell back to a Chrome WebDriver session. `proxyUnawareApp` was then sent to Chrome (not Appium), which rejected it as `invalid locator`. The `.env` file fixes this by ensuring all `${VAR}` placeholders are resolved before the SDK starts.

---

## 4. Run modes

### Mode A — No SDK, PyCharm play button

1. Open `Run_Local_Debugger_Wikipedia.py` (Wikipedia) or `Run_Local_Debugger.py` (AAFES) in PyCharm.
2. Click the green play button.

PyCharm runs pytest directly. `Initializer.get_driver()` creates the Appium session using credentials from `.env`. `proxyUnawareApp: true` is passed in `bstack:options`.

**PyCharm interpreter:** Go to `Settings > Project > Python Interpreter` and select `.venv/bin/python` so `python-dotenv` is available and `.env` is loaded.

---

### Mode B — No SDK, terminal

```bash
# Verify infra with Wikipedia
pytest Run_Local_Debugger_Wikipedia.py::TestLocalWikipedia

# AAFES login test
pytest Run_Local_Debugger.py::TestLocal
```

---

### Mode C — With SDK, local

```bash
# Wikipedia
python Run_Config_Wikipedia.py

# AAFES smoke suite
python Run_Config_Android.py
```

Or directly:

```bash
browserstack-sdk pytest --config browserstack_android.yml smoke/test_keepmesignedin.py
```

`Run_Config_*.py` loads `.env` via `python-dotenv`, exports all values to `os.environ`, then spawns the SDK subprocess. The SDK reads `BROWSERSTACK_USERNAME`, `BROWSERSTACK_ACCESS_KEY`, and all `${VAR}` placeholders from `os.environ`. `proxyUnawareApp: true` is in the YML and passed to BrowserStack automatically.

---

### Mode D — CI pipeline

Set these as pipeline secrets:

```
BROWSERSTACK_USERNAME=your_username
BROWSERSTACK_ACCESS_KEY=your_access_key
AppURL=bs://YOUR_AAFES_APP_URL_HERE
PlatformType=android
DeviceName=Samsung Galaxy S23
DeviceVersion=13.0
SESSION_NAME=test_keepmesignedin
BUILD_NAME=MEA | Smoke | android
BUILD_NUMBER=${BUILD_NUMBER}
APP_USERNAME=automlplus01
APP_PASSWORD=Aafes123#
```

Run:

```bash
python Run_Config_Android.py
```

No `.env` file needed in CI. `python-dotenv` uses `override=False` so pipeline vars always win.

---

## 5. Verify infra first (Wikipedia test)

Before running the AAFES login test, verify the infrastructure works:

```bash
pytest Run_Local_Debugger_Wikipedia.py::TestLocalWikipedia
```

Expected: **1 passed** — Wikipedia app launches, Search bar visible, Explore tab present.

If this passes, credentials, app URL, device config, and `proxyUnawareApp` are all working correctly.

---

## 6. File reference

| File | Purpose |
|---|---|
| `env.example` | Template — copy to `.env` |
| `Initializer.py` | No-SDK session creation; `proxyUnawareApp: true` in `bstack:options` |
| `conftest.py` | Root conftest for SDK mode |
| `smoke/conftest.py` | Minimal conftest for standalone pytest runs |
| `browserstack_android.yml` | SDK caps for AAFES app; `proxyUnawareApp: true` |
| `browserstack_wikipedia.yml` | SDK caps for Wikipedia sample; `proxyUnawareApp: true` |
| `Run_Local_Debugger.py` | No-SDK runner for AAFES tests |
| `Run_Local_Debugger_Wikipedia.py` | No-SDK runner for Wikipedia test |
| `Run_Config_Android.py` | SDK suite runner for AAFES smoke |
| `Run_Config_Wikipedia.py` | SDK runner for Wikipedia sample |
| `smoke/test_keepmesignedin.py` | Customer login test |
| `smoke/test_wikipedia_sample.py` | Wikipedia infra verification test |

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `invalid locator` + `Session info: chrome=114` | SDK fell back to Chrome — `AppURL` not set | Set `AppURL` in `.env` before running |
| `Invalid username or password` | `.env` not loaded | Set PyCharm interpreter to `.venv`; check `.env` credentials |
| `Re-run N` on dashboard | Static `BUILD_NUMBER` | Fixed — `buildName` now always includes a timestamp |
| `Untitled` build name | `BUILD_NAME` not in `.env` | Add `BUILD_NAME=MEA | Smoke | android` to `.env` |
| `Authorization Required` | Credentials not loaded | Check `.env` has `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY` |
| App network errors / proxy issues | `proxyUnawareApp` missing | Confirmed present in all 3 run modes — see Section 3 |