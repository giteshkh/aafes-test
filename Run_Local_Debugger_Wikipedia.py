"""
Run_Local_Debugger_Wikipedia.py
================================
Local (NO SDK) runner for the Wikipedia sample test.

Mirrors Run_Local_Debugger.py exactly — uses Initializer.get_driver()
directly so no browserstack-sdk wrapper is needed.

.env support
------------
python-dotenv is loaded at the top so that a .env file at the project root
is automatically picked up. Copy env.example to .env and fill in your values.

Usage (from the project root):
    pytest Run_Local_Debugger_Wikipedia.py::TestLocalWikipedia

Change `params=[4]` to any index from Initializer.devices[] to pick a
different device.  Index 4 = Samsung Galaxy S23 Ultra / 13.0.
"""

import os

# ── Load .env using absolute path so PyCharm's play button works too ─────────
try:
    import pathlib
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=pathlib.Path(__file__).resolve().parent / ".env",
                override=False)
except ImportError:
    pass

import pytest
from Initializer import Initializer

# NOTE: TestWikipediaSample is imported INSIDE the test method (not at module
# level) so that pytest does not collect it twice when running this file.
# A module-level import would cause pytest to discover TestWikipediaSample
# here AND in smoke/test_wikipedia_sample.py, running it without a driver.


class TestLocalWikipedia:

    @pytest.fixture(scope="module",
                    params=[4])   # index into Initializer.devices[]
    def driver(self, request):
        """
        Create a direct Appium session via Initializer (no SDK).
        The driver is shared across all tests in this module.
        """
        device_index = request.param
        driver_instance = Initializer.get_driver(device_index=device_index)
        yield driver_instance
        driver_instance.quit()

    @pytest.fixture(scope="module")
    def request_fixture(self, request):
        return request

    # ------------------------------------------------------------------ #
    # Inject driver into request.node so the test class can use the same  #
    # `request.node.driver` pattern as the SDK conftest does.             #
    # ------------------------------------------------------------------ #

    def _make_mock_request(self, driver):
        """Return a mock request whose .node.driver points to `driver`."""

        class _MockNode:
            def __init__(self, d):
                self.driver = d

        class _MockRequest:
            def __init__(self, d):
                self.node = _MockNode(d)

        return _MockRequest(driver)

    # ------------------------------------------------------------------ #

    def test_wikipedia_local(self, driver, request_fixture):
        """
        Entry point — delegates to TestWikipediaSample using a mock request
        so the test class is identical whether run locally or via SDK.
        """
        # Import here (not at module level) to prevent pytest from collecting
        # TestWikipediaSample when it scans this file.
        from smoke.test_wikipedia_sample import TestWikipediaSample

        session_id = driver.session_id
        mock_request = self._make_mock_request(driver)

        try:
            test_instance = TestWikipediaSample()
            test_instance.test_wikipedia_first_screen_SME_WIKI_001(mock_request)
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            session_url = Initializer.get_session_url(session_id)
            print(f"Test session URL: {session_url}")