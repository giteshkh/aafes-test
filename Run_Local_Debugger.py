"""
Run_Local_Debugger.py
=====================
Customer's original local (NO SDK) runner.

.env support added: python-dotenv is loaded at the top using an absolute
path so PyCharm's green-play button finds .env regardless of cwd.

Usage (from the project root):
    pytest Run_Local_Debugger.py::TestLocal

Change `params=[4]` to any index from Initializer.devices[] to pick a
different device.  Index 4 = Samsung Galaxy S23 Ultra / 13.0.

NOTE: This file imports TestHome and TestGeneric from the customer's full
project. When running in this sample repo, replace those imports with your
own test class and method.
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

# ── Customer's test imports ───────────────────────────────────────────────────
# Replace these with your actual test class imports.
# In the customer's full project these resolve to:
#   from sanity.test_sanity_Home import TestHome
#   from tests.test_Generic import TestGeneric
#
# For this sample repo we import the Wikipedia test as a stand-in.
# To test the customer's login flow, replace with:
#   from smoke.test_keepmesignedin import TestKeepMeSignedIN
try:
    from smoke.test_keepmesignedin import TestKeepMeSignedIN as TestClass
    _TEST_METHOD = "test_keep_me_signed_in_SME_14343"
    _USE_KEEPMESIGNEDIN = True
except ImportError:
    from smoke.test_wikipedia_sample import TestWikipediaSample as TestClass
    _TEST_METHOD = "test_wikipedia_first_screen_SME_WIKI_001"
    _USE_KEEPMESIGNEDIN = False


class TestLocal:

    @pytest.fixture(scope='module',
                    params=[4])  # Update params as needed for different devices
    def driver(self, request):
        device_index = request.param
        driver_instance = Initializer.get_driver(device_index=device_index)
        yield driver_instance
        driver_instance.quit()

    @pytest.fixture(scope='module')
    def request_fixture(self, request):
        return request

    def _make_mock_request(self, driver):
        class _MockNode:
            def __init__(self, d):
                self.driver = d

        class _MockRequest:
            def __init__(self, d):
                self.node = _MockNode(d)

        return _MockRequest(driver)

    def run_test(self, request, driver):
        mock_request = self._make_mock_request(driver)
        test_instance = TestClass()
        getattr(test_instance, _TEST_METHOD)(mock_request)

    def test_local(self, driver, request_fixture):
        session_id = driver.session_id
        try:
            self.run_test(request_fixture, driver)
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            session_url = Initializer.get_session_url(session_id)
            print(f"Test session URL: {session_url}")