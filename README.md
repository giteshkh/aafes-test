# AAFES MEA — run the Wikipedia test and the sign-in test on BrowserStack

Two ways to run the same tests from PyCharm:

| | Legacy (no SDK) | SDK |
|---|---|---|
| Entry point | `Run_Local_Debugger_Wikipedia.py` / `Run_Local_Debugger.py` | the same files, launched through `browserstack-sdk` |
| Capabilities come from | `Initializer.py` | `browserstack_android.yml` **merged with** `Initializer.py` |
| Accessibility / screen reader settings | not applied | applied (from `browserstack_android.yml`) |

Use one config file for both: `browserstack_android.yml`.

---

## 1. Setup

Install dependencies (Python 3.9+):

```bash
pip install -r requirements.txt
```

Copy `env.example` to `.env` (it is git-ignored) and fill it in:

```bash
cp env.example .env
```

```
BROWSERSTACK_USERNAME=<your BrowserStack username>
BROWSERSTACK_ACCESS_KEY=<your BrowserStack access key>
AppURL=bs://<your app id>
PlatformType=android
DeviceName=Samsung Galaxy S23
DeviceVersion=13.0
SESSION_NAME=wikipedia_local
BUILD_NAME=MEA | Wikipedia | Debug
BUILD_NUMBER=1
PROXY_UNAWARE_APP=false
APP_USERNAME=<sign-in test account username>
APP_PASSWORD=<sign-in test account password>
```

Quote values that contain spaces if you `source` the file in a shell. The code loads `.env` itself where it needs to.

### What you must change in the code (marked `>>> CUSTOMER:`)

| File | What to change |
|---|---|
| `Initializer.py` | `APP_URL` is hardcoded and is used directly by the legacy path. It is set to the Wikipedia sample `bs://2cb25d26…`. Put your own app id there (yours was `bs://1548e810891c53f18254d1d04527e7e3e854e442`). |
| `browserstack_android.yml` | `proxyUnawareApp` is `false` so the Wikipedia app runs. Set it back to `true` for your AAFES app if it needs it. |
| `.env` | `APP_USERNAME` / `APP_PASSWORD` for the sign-in test (no longer hardcoded in `smoke/test_keepmesignedin.py`). |

Rotate any credentials that were previously hardcoded in the files you shared.

---

## 2. Legacy run (no SDK)

PyCharm: open `Run_Local_Debugger_Wikipedia.py` (Wikipedia) or `Run_Local_Debugger.py` (sign-in), then use the normal run/debug button. The interpreter must be the project's `.venv`.

Terminal:

```bash
python -m pytest -s Run_Local_Debugger_Wikipedia.py
```

Notes:
- The session is created by `Initializer.get_driver()`.
- The autouse fixture in `conftest.py` also creates a driver from `browserstack_android.yml`, so a legacy run opens two BrowserStack sessions. The test uses the one from `Initializer`.
- `conftest.py` fills the yml's `${VAR}` placeholders from environment variables when the SDK is not running, so `PlatformType`, `DeviceName`, `DeviceVersion` and `AppURL` must be set (in `.env` or the run configuration).

---

## 3. SDK run (PyCharm)

Create one **Python** run/debug configuration (not "Python tests"):

| Field | Value |
|---|---|
| Run type | `script` (change the dropdown from `module`) |
| Script path | `<project>/.venv/bin/browserstack-sdk` (this path only, no arguments) |
| Script parameters | `pytest -s $FilePath$` |
| Working directory | the project root |
| Python interpreter | the project's `.venv` |
| Environment variables | `PYTHONUNBUFFERED=1;BROWSERSTACK_CONFIG_FILE=browserstack_android.yml;
| Paths to ".env" files | leave empty |

To run: open `Run_Local_Debugger_Wikipedia.py` (or `Run_Local_Debugger.py`) in the editor and press Run or Debug on this configuration. `$FilePath$` passes the open file to pytest.

Terminal equivalent:

```bash
BROWSERSTACK_CONFIG_FILE=browserstack_android.yml .venv/bin/browserstack-sdk pytest -s Run_Local_Debugger_Wikipedia.py
```

`BROWSERSTACK_USERNAME`, `BROWSERSTACK_ACCESS_KEY` and `AppURL` must also be in the environment. `conftest.py` and `Initializer.py` load `.env` themselves, but export them in the shell to be safe.

What to expect:
- The log shows `claimed leader role`, `collected 1 item` and `1 passed`.
- The dashboard build and session names come from `browserstack_android.yml`.
- Accessibility scanning shows up as `AccessibilityModule ... running 1 scripts` lines in the log.

Where the SDK takes capabilities from:
- `browserstack_android.yml` sets build, session and project names, device, OS version, app, `appProfiling` and all accessibility options.
- Capabilities the yml does not set (`noReset`, video, `percyOptions` and others) still come from `Initializer.py`.
- For a capability set in both, test results showed the `Initializer` value reached the hub in one case (`idleTimeout`).

---

## 4. Accessibility and screen reader settings

They live only in `browserstack_android.yml` and apply only to SDK runs:

```yaml
accessibility: true
accessibilityOptions:
  wcagVersion: wcag21aaa
  screenReaderAutomation:
    autoReport: true
    linearNavigation: true
    linearNavigationTimeout: 300000
```

The SDK scan was confirmed in the logs. The screen reader report itself was not confirmed on the dashboard, and the BrowserStack docs list Screen Reader Automation under the Ultimate plan.

---

## 5. The AAFES runner and the sign-in test

`Run_Local_Debugger.py` (your original runner) imports `sanity.test_sanity_Home` and `tests.test_Generic`, and `smoke/test_keepmesignedin.py` imports `objrepo`, `tests.test_Generic`, `utils.appium_utils` and `utils.general_utils`. None of these are in this repo, so both only run in your full project. Neither was run here; only `Run_Local_Debugger_Wikipedia.py` and the Wikipedia tests were.

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Authorization Required` | credentials not set | set `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY` |
| `BROWSERSTACK_INVALID_APP_URL` | the app id is not on your account | set a valid id in `Initializer.py` (legacy) and `AppURL` |
| `BROWSERSTACK_INVALID_PLATFORM_NAME_DDA` | `PlatformType`, `DeviceName` or `DeviceVersion` not set | set them |
| `PROXY_UNAWARE_OS_NOT_SUPPORTED` | `proxyUnawareApp: true` with an app that cannot use it | set it to `false` for that app |
| `FileNotFoundError` in PyCharm | arguments typed into the script path | put only the SDK path there; the rest in Script parameters |
| SDK exits at once with `follower joined leader`, no pytest output | stale SDK sockets from an earlier run | `rm -f /tmp/sdk-platform-*.sock` when no SDK run is in progress |