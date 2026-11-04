"""
Wikipedia Sample Test — smoke/test_wikipedia_sample.py

Validates that the Wikipedia app launches and the Explore (feed) screen
is visible with the Search bar present.

Execution modes
---------------
1. Via SDK (CI or local with SDK):
       browserstack-sdk pytest --config browserstack.yml smoke/test_wikipedia_sample.py

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

import pytest
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


from utils.test_data import get_row_data


class TestWikipediaSample:
    """
    Validates the Wikipedia app first screen (Explore / Feed).
    No login, no navigation — just launch and assert.
    """

    def test_row_data_picked_up_SME_WIKI_000(self, request):
        """Stub validation: the xlsx row passed by Run_Config via TEST_ROW_DATA
        reaches the test and matches the test being run (apples-to-apples with
        the customer's data flow)."""
        data = get_row_data()
        assert data, "TEST_ROW_DATA is empty — Run_Config did not pass the row"
        assert data.get("RunMode") == "Y", f"RunMode should be 'Y', got '{data.get('RunMode')}'"
        assert data.get("TestCaseId") == request.node.name, (
            f"TestCaseId '{data.get('TestCaseId')}' should equal running test '{request.node.name}'"
        )
        # Per-iteration values: each xlsx row carries its own RowId, and Username /
        # ExpectedSearchHint are derived from it, proving each iteration received
        # its own data rather than a stale or shared row.
        row_id = data.get("RowId", "")
        assert row_id.isdigit(), f"RowId should be numeric, got '{row_id}'"
        assert data.get("Username") == f"wiki_user_{row_id}", (
            f"Username should be 'wiki_user_{row_id}' for row {row_id}, got '{data.get('Username')}'"
        )
        assert data.get("Itemid") == f"ITEM-{row_id}", (
            f"Itemid should be 'ITEM-{row_id}' for row {row_id}, got '{data.get('Itemid')}'"
        )
        assert data.get("ClassName") == type(self).__name__, (
            f"ClassName '{data.get('ClassName')}' should equal '{type(self).__name__}'"
        )
        for key in ("Username", "Password", "ExpectedSearchHint", "Login_Yes_No"):
            assert key in data, f"Test data column '{key}' missing from TEST_ROW_DATA"
        print(f"[test-data] picked up row: { {k: ('***' if k == 'Password' else v) for k, v in data.items()} }")

    # ------------------------------------------------------------------ #
    # Selectors (derived from get_page_source on Samsung Galaxy S23)      #
    # ------------------------------------------------------------------ #
    _SEARCH_CONTAINER_ID = "org.wikipedia.alpha:id/search_container"
    _SEARCH_HINT_TEXT    = "Search Wikipedia"
    _EXPLORE_TAB_DESC    = "Explore"
    _FEED_RECYCLER_ID    = "org.wikipedia.alpha:id/fragment_feed_feed"
    _MY_LISTS_TAB_DESC   = "My lists"
    _HISTORY_TAB_DESC    = "History"
    _NEARBY_TAB_DESC     = "Nearby"
    _MY_LISTS_EMPTY_ID   = "org.wikipedia.alpha:id/empty_title"
    _HISTORY_EMPTY_ID    = "org.wikipedia.alpha:id/history_empty_title"
    _TOOLBAR_TITLE_XPATH = (
        # Toolbar title TextView has no resource-id or content-desc in the page
        # source, so it can only    be located structurally. It is a DIRECT child of
        # the toolbar; the menu icons (search/sort) sit in a nested
        # LinearLayoutCompat, so a descendant '//' match would be ambiguous.
        '//*[@resource-id="org.wikipedia.alpha:id/single_fragment_toolbar"]'
        '/android.widget.TextView'
    )
    _NEARBY_MAP_ID       = "org.wikipedia.alpha:id/mapview"
    # ------------------------------------------------------------------ #

    def _get_driver(self, request):
        """Return the injected driver or skip when none is available."""
        if not hasattr(request.node, "driver") or request.node.driver is None:
            pytest.skip("No driver injected — run via Run_Local_Debugger_Wikipedia.py "
                        "or smoke/conftest.py")
        return request.node.driver

    def _open_tab(self, driver, tab_desc):
        """Tap a bottom-nav tab by its accessibility id."""
        wait = WebDriverWait(driver, 20)
        tab = wait.until(
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, tab_desc))
        )
        tab.click()

    def _text_of(self, driver, by, value):
        wait = WebDriverWait(driver, 20)
        return wait.until(EC.presence_of_element_located((by, value))).text

    def test_wikipedia_my_lists_empty_state_SME_WIKI_002(self, request):
        """My lists tab shows the empty state for a fresh install."""
        driver = self._get_driver(request)
        self._open_tab(driver, self._MY_LISTS_TAB_DESC)

        title = self._text_of(driver, AppiumBy.XPATH, self._TOOLBAR_TITLE_XPATH)
        assert title == "My lists", f"Expected toolbar title 'My lists', got '{title}'"

        empty_title = self._text_of(driver, AppiumBy.ID, self._MY_LISTS_EMPTY_ID)
        assert empty_title == "No reading lists yet", (
            f"Expected 'No reading lists yet', got '{empty_title}'"
        )

    def test_wikipedia_history_empty_state_SME_WIKI_003(self, request):
        """History tab shows the empty state for a fresh install."""
        driver = self._get_driver(request)
        self._open_tab(driver, self._HISTORY_TAB_DESC)

        title = self._text_of(driver, AppiumBy.XPATH, self._TOOLBAR_TITLE_XPATH)
        assert title == "History", f"Expected toolbar title 'History', got '{title}'"

        empty_title = self._text_of(driver, AppiumBy.ID, self._HISTORY_EMPTY_ID)
        assert empty_title == "No recently viewed articles", (
            f"Expected 'No recently viewed articles', got '{empty_title}'"
        )

    def test_wikipedia_nearby_screen_SME_WIKI_004(self, request):
        """Nearby tab loads the map view."""
        driver = self._get_driver(request)
        self._open_tab(driver, self._NEARBY_TAB_DESC)

        title = self._text_of(driver, AppiumBy.XPATH, self._TOOLBAR_TITLE_XPATH)
        assert title == "Nearby", f"Expected toolbar title 'Nearby', got '{title}'"

        wait = WebDriverWait(driver, 20)
        assert wait.until(
            EC.presence_of_element_located((AppiumBy.ID, self._NEARBY_MAP_ID))
        ) is not None, "Nearby map view not found"

    def test_wikipedia_tab_round_trip_SME_WIKI_005(self, request):
        """Navigate across all tabs and back to Explore; the feed is shown again."""
        driver = self._get_driver(request)
        for tab in (self._MY_LISTS_TAB_DESC, self._HISTORY_TAB_DESC,
                    self._NEARBY_TAB_DESC, self._EXPLORE_TAB_DESC):
            self._open_tab(driver, tab)

        # Returning to Explore can leave the feed list scrolled, so the search bar
        # and first card header are not always in the view hierarchy (captured at the
        # failing wait: the feed container and the lower cards were present, the
        # search bar was not). Assert on the container, which is always there.
        wait = WebDriverWait(driver, 20)
        feed = wait.until(
            EC.presence_of_element_located((AppiumBy.ID, self._FEED_RECYCLER_ID))
        )
        assert feed.is_displayed(), (
            "Feed RecyclerView exists but is not displayed after returning to Explore"
        )

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
            expected_hint = get_row_data().get("ExpectedSearchHint", self._SEARCH_HINT_TEXT)
            assert actual_text == expected_hint, (
                f"Expected search hint '{expected_hint}' (from test data), got '{actual_text}'"
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