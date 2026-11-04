# MEA setup — changes needed to reproduce the working run

Everything below is the delta between the files in `MEA_script_set_up_files 4`
and the versions that ran successfully on BrowserStack App Automate
(SDK 1.61.2, Python 3.9). Anything not listed was left unchanged.

Two ways to run are supported and both were verified:

| Mode | Command | What supplies capabilities |
|---|---|---|
| **SDK injected** | `browserstack-sdk pytest -s <test file>` | `browserstack_android.yml` (build, session, device, app, accessibility) **merged with** the legacy caps in `Initializer.py` |
| **Legacy (no SDK)** | `python -m pytest -s <test file>` | `Initializer.py` caps and device list only. The yml's accessibility settings do **not** apply |

---

## 1. Credentials: move them out of the code

Rotate the BrowserStack key and the test-account password that were hardcoded in the
files you sent. They have been shared in clear text.

Create a git-ignored `.env` in the project root:

```
BROWSERSTACK_USERNAME=<your username>
BROWSERSTACK_ACCESS_KEY=<your access key>
AppURL=bs://<your app id>
APP_USERNAME=<app test user>
APP_PASSWORD=<app test password>
```

Load it before running (`set -a; source .env; set +a`), or use PyCharm's
"Paths to .env files" / environment variables field.
Values containing spaces must be quoted when sourced from a shell.

## 2. `browserstack_android.yml`

| Line | Was | Now | Why |
|---|---|---|---|
| `userName` | literal username | `${BROWSERSTACK_USERNAME}` | no secrets in the file |
| `accessKey` | literal key | `${BROWSERSTACK_ACCESS_KEY}` | no secrets in the file |
| `browserstack.idleTimeout: 400` | dotted key | `idleTimeout: 400` | the hub rejects `browserstack.idleTimeout` inside `bstack:options` |
| `proxyUnawareApp: true` | true | `false` for non-AAFES apps | the hub returns `PROXY_UNAWARE_OS_NOT_SUPPORTED` for apps that cannot run with it. **Keep `true` for the AAFES app** if it needs it |

Append this block to turn on App Accessibility with the screen reader report:

```yaml
accessibility: true
accessibilityOptions:
  wcagVersion: wcag21aaa
  screenReaderAutomation:
    autoReport: true
    linearNavigation: true
    linearNavigationTimeout: 300000
  includeIssueType:
    bestPractice: true
    needsReview: true
    experimentalRules: true
```

Notes:
- Screen Reader Automation is documented as **Ultimate plan only**. Without that plan no
  screen reader report is produced even with this config.
- The SDK reads only the file named by `BROWSERSTACK_CONFIG_FILE` (set to `browserstack_android.yml`).
  `accessibility: true` must be in that file, not a different yml.
- `wcag21aaa` follows the naming of the documented `wcag22aaa` example. Confirm the
  WCAG level shown on the dashboard.

## 3. `Initializer.py`

```python
USERNAME = os.environ.get('BROWSERSTACK_USERNAME', '')
ACCESS_KEY = os.environ.get('BROWSERSTACK_ACCESS_KEY', '')
APP_URL = 'bs://<your app id>'   # was hardcoded; keep your own app id here
```

Nothing else changed. The legacy caps (`noReset`, `ensureWebviewsHavePages`,
`connectHardwareKeyboard`, `browserstack.video`, `percyOptions`) still reach the hub when the SDK is used.

## 4. `conftest.py`

Needed only so the **legacy (no-SDK) path** works, because without the SDK the yml's
`${VAR}` placeholders are never substituted. Both changes are no-ops when the SDK runs.

```python
def load_browserstack_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return _resolve_env_placeholders(config)

def _resolve_env_placeholders(value):
    if isinstance(value, dict):
        return {k: _resolve_env_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_placeholders(v) for v in value]
    if isinstance(value, str):
        return os.path.expandvars(value)
    return value
```

and in `create_driver_from_config`, replace the `hub_url = ...` line with:

```python
user_name = config['userName']
access_key = config['accessKey']
if str(user_name).startswith("${"):
    user_name = os.environ.get("BROWSERSTACK_USERNAME", user_name)
if str(access_key).startswith("${"):
    access_key = os.environ.get("BROWSERSTACK_ACCESS_KEY", access_key)
hub_url = f"https://{user_name}:{access_key}@hub-cloud.browserstack.com/wd/hub"
```

## 5. `Run_Config_Android.py` (Windows paths)

```python
project_root = os.path.dirname(os.path.abspath(__file__))          # was get_project_root() + "\\appium_BrowserStack"
os.environ['PYTHONPATH'] = f'{project_root}{os.pathsep}' + os.getenv('PYTHONPATH', '')   # was f'{project_root};'
```

Only needed on macOS/Linux. On Windows the original lines work.

## 6. `test_keepmesignedin.py`

```python
import os
User_Name = os.environ.get("APP_USERNAME", "")
User_Password = os.environ.get("APP_PASSWORD", "")
```

## 7. `Run_Local_Debugger.py`

No change.

---

## Environment variables the yml placeholders need

```
BROWSERSTACK_CONFIG_FILE=browserstack_android.yml
PlatformType=android
DeviceName=Samsung Galaxy S23
DeviceVersion=13.0
AppURL=bs://<your app id>
SESSION_NAME=<session name>
BUILD_NAME=<build name>
BUILD_NUMBER=1
```

Without `PlatformType`, `DeviceName` and `DeviceVersion` the hub fails with
`BROWSERSTACK_INVALID_PLATFORM_NAME_DDA`.

## Running

**With the SDK**

```bash
browserstack-sdk pytest -s Run_Local_Debugger.py
```

In PyCharm: a **Python** (not "Python tests") run/debug configuration with
script path `<project>/.venv/bin/browserstack-sdk`, script parameters
`pytest -s $FilePath$`, working directory = project root, and the environment variables above.
Use the Python interpreter of the project's `.venv`.
A fixed script path with the arguments in "Script parameters" avoids `FileNotFoundError`.

**Legacy (no SDK)**

```bash
python -m pytest -s Run_Local_Debugger.py
```

## Things to know

- **Two sessions per legacy run.** The autouse fixture in `conftest.py` creates a driver
  from the yml and `Initializer.get_driver()` creates a second one. The test uses the
  second. The first session is created and not used by the test.
- **Stale SDK sockets.** If an SDK run exits immediately with `follower joined leader`
  and no pytest output, remove leftovers with `rm -f /tmp/sdk-platform-*.sock`
  (only when no SDK run is in progress).
- **SDK version.** Verified on 1.61.2 (the `-latest` tarball at the time). 1.55.2 also
  worked for the same config. Upgrading the SDK also upgraded `selenium` (4.21.0 to 4.36.0)
  and other dependencies.
- **Where capabilities come from with the SDK:** the yml sets build/session/project names,
  device, OS version, app, `appProfiling` and all accessibility options. Legacy
  `Initializer` caps the yml does not set are still sent. For a cap set in both places
  (for example `idleTimeout`), the legacy value was the one the hub received in testing.
