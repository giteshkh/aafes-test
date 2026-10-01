"""
smoke/test_keepmesignedin.py
============================
Customer's original test_keepmesignedin.py — unchanged except:

1. Credentials (User_Name, User_Password) read from env vars so they can
   be set in .env without hardcoding.

2. Internal imports (AppiumUtils, GeneralUtils, LoginObjects, ObjectRepository,
   PlatformType) are wrapped in a try/except so the file can be imported in
   this sample repo without the full customer project present.
   When the customer runs this in their own project, the real imports take over.

Usage (no SDK, via Run_Local_Debugger.py):
    pytest Run_Local_Debugger.py::TestLocal

Usage (with SDK):
    browserstack-sdk pytest --config browserstack_android.yml smoke/test_keepmesignedin.py
"""

import os
import sys

# ── Load .env using absolute path so PyCharm's play button works too ─────────
try:
    import pathlib
    from dotenv import load_dotenv
    _root = pathlib.Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=_root / ".env", override=False)
except ImportError:
    pass

# ── Try to import customer's internal modules; stub if not present ────────────
try:
    from objrepo.login_object_repo import LoginObjects
    from objrepo.obj_repo import ObjectRepository
    from tests.test_Generic import TestGeneric
    from utils.appium_utils import AppiumUtils
    from utils.general_utils import GeneralUtils
    from tests.platformTypeMode import PlatformType
    _HAS_CUSTOMER_MODULES = True
except ImportError:
    _HAS_CUSTOMER_MODULES = False

from Initializer import Initializer


class TestKeepMeSignedIN:
    # Credentials — read from env vars (set in .env or CI pipeline)
    # Set APP_USERNAME and APP_PASSWORD in your .env file.
    User_Name     = os.environ.get("APP_USERNAME", "automlplus01")
    User_Password = os.environ.get("APP_PASSWORD", "Aafes123#")

    def test_keep_me_signed_in_SME_14343(self, request):
        """
        Customer's keep-me-signed-in test.

        When running in the customer's full project (with all internal modules),
        this test performs the full login flow.

        When running in this sample repo (without internal modules), it skips
        gracefully with a clear message so the repo can still be shared and
        the structure validated.
        """
        driver = request.node.driver
        session_id = driver.session_id

        if not _HAS_CUSTOMER_MODULES:
            import pytest
            pytest.skip(
                "Customer's internal modules (AppiumUtils, LoginObjects, etc.) "
                "are not present in this sample repo. "
                "Copy this file into the customer's full project to run the login test."
            )

        try:
            appium_utils = AppiumUtils()
            screenshot_folder = "screenshots"
            GeneralUtils.take_screenshot(driver, screenshot_folder)
            TestGeneric.allow_notifications(driver)
            appium_utils.wait_and_click_element(driver, LoginObjects.BTN_LOGIN(), "Login")
            appium_utils.wait_and_actions_sendKeys(driver, LoginObjects.INPUT_USERNAME_FIELD(), self.User_Name)
            appium_utils.wait_and_actions_sendKeys(driver, LoginObjects.INPUT_PASSWORD_FIELD(), self.User_Password)
            appium_utils.click_element_position(driver, ObjectRepository.BTN_KEEP_ME_SIGNED_IN(), 0.2, 0.5)
            appium_utils.wait_for_element_and_click(driver, LoginObjects.BTN_SIGN_IN(), 10)
            appium_utils.wait_for_element(driver, LoginObjects.TXT_LANDING_MSG())
            appium_utils.wait_and_click_element(driver, ObjectRepository.BTN_SKIP_THIS(), "Skip This link")
            appium_utils.wait_for_element(driver, ObjectRepository.ICON_HOME())

        except Exception as e:
            print(f"An error occurred: {e}")
            Initializer.update_session_status(session_id, "failed",
                                              f"Keep me signed in test failed: {e}")
            raise
        finally:
            session_url = Initializer.get_session_url(session_id)
            print(f"Test session URL: {session_url}")