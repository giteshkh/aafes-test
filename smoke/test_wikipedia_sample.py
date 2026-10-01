"""
Wikipedia Sample Test — smoke/test_wikipedia_sample.py

Validates that the Wikipedia app launches and the Explore (feed) screen
is visible with the Search bar present.

Execution modes
---------------
1. Via SDK (CI or local with SDK):
       browserstack-sdk pytest --config browserstack_wikipedia.yml smoke/test_wikipedia_sample.py

2. Via Run_Config_Wikipedia.py (SDK, suite runner):
       python Run_Config_Wikipedia.py

3. Via Run_Local_Debugger_Wikipedia.py (NO SDK, direct Appium):
       pytest Run_Local_Debugger_Wikipedia.py::TestLocalWikipedia

The test uses `request.node.driver` which is injected by conftest.py
(SDK mode) or by the local debugger fixture (non-SDK mode).

.env support
------------
All credentials and device values are read from environment variables.
Copy env.example to .env and fill in your values — no code changes needed.
"""

import sys
import os

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Ensure project root is on sys.path so Initializer resolves correctly ─────
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

# ── Load .env (no-op if already loaded by conftest or if file doesn't exist) ─
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(_root, ".env"), override=False)
except ImportError:
    pass

# Initializer is optional — present in the customer's full project,
# absent when running this sample standalone.
try:
    from Initializer import Initializer
    _HAS_INITIALIZER = True
except ImportError:
    _HAS_INITIALIZER = False


class TestWikipediaSample:
    """
    Validates the Wikipedia app first screen (Explore / Feed).
    No login, no navigation — just launch and assert.
    """

    # ------------------------------------------------------------------ #
    # Selectors (derived from get_page_source on Samsung Galaxy S23)      #
    # ------------------------------------------------------------------ #
    _SEARCH_CONTAINER_ID = "org.wikipedia.alpha:id/search_container"
    _SEARCH_HINT_TEXT    = "Search Wikipedia"
    _EXPLORE_TAB_DESC    = "Explore"
    _FEED_RECYCLER_ID    = "org.wikipedia.alpha:id/fragment_feed_feed"
    # ------------------------------------------------------------------ #

    def test_wikipedia_first_screen_SME_WIKI_001(self, request):
        """
        Verify the Wikipedia app launches and the Explore feed is visible.

        Steps
        -----
        1. Obtain the driver injected by conftest (SDK) or local fixture.
        2. Wait for the Search bar to appear — confirms the feed screen loaded.
        3. Assert the Search bar hint text is "Search Wikipedia".
        4. Assert the Explore bottom-nav tab is present.
        5. Assert the feed RecyclerView is present.
        """
        # When run directly by pytest (not via Run_Local_Debugger_Wikipedia.py),
        # request.node.driver may not be set — skip gracefully in that case.
        if not hasattr(request.node, "driver") or request.node.driver is None:
            pytest.skip("No driver injected — run via Run_Local_Debugger_Wikipedia.py "
                        "or smoke/conftest.py")
        driver = request.node.driver
        session_id = driver.session_id

        try:
            wait = WebDriverWait(driver, 20)

            # Step 2 — wait for search container
            search_container = wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.ID, self._SEARCH_CONTAINER_ID)
                )
            )
            assert search_container is not None, (
                "Search container not found — app may not have launched correctly"
            )

            # Step 3 — assert search hint text
            search_hint = wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.ANDROID_UIAUTOMATOR,
                     f'new UiSelector().text("{self._SEARCH_HINT_TEXT}")')
                )
            )
            actual_text = search_hint.text
            assert actual_text == self._SEARCH_HINT_TEXT, (
                f"Expected search hint '{self._SEARCH_HINT_TEXT}', got '{actual_text}'"
            )

            # Step 4 — assert Explore bottom-nav tab
            explore_tab = wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.ACCESSIBILITY_ID, self._EXPLORE_TAB_DESC)
                )
            )
            assert explore_tab is not None, "Explore tab not found in bottom navigation"

            # Step 5 — assert feed RecyclerView loaded
            feed = wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.ID, self._FEED_RECYCLER_ID)
                )
            )
            assert feed is not None, "Feed RecyclerView not found — feed may not have loaded"

            print("PASS: Wikipedia first screen validated successfully")
            if _HAS_INITIALIZER:
                Initializer.update_session_status(
                    session_id, "passed", "Wikipedia first screen validated"
                )

        except Exception as e:
            print(f"An error occurred: {e}")
            if _HAS_INITIALIZER:
                Initializer.update_session_status(
                    session_id, "failed",
                    f"Wikipedia first screen test failed: {e}"
                )
            raise

        finally:
            if _HAS_INITIALIZER:
                session_url = Initializer.get_session_url(session_id)
            else:
                session_url = (
                    f"Dashboard: https://app-automate.browserstack.com"
                    f"/dashboard/v2/sessions/{session_id}"
                )
            print(f"Test session URL: {session_url}")