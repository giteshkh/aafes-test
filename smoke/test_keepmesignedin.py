import os
import time

from selenium.webdriver.common.by import By
from objrepo.login_object_repo import LoginObjects
from objrepo.obj_repo import ObjectRepository
from Initializer import Initializer
from tests.test_Generic import TestGeneric
from utils.appium_utils import AppiumUtils
from utils.general_utils import GeneralUtils
from tests.platformTypeMode import PlatformType

appium_utils_instance = AppiumUtils()
class TestKeepMeSignedIN:
    # >>> CUSTOMER: credentials are no longer hardcoded here. <<<
    # Set APP_USERNAME and APP_PASSWORD in your .env (or the PyCharm run config's
    # environment variables) with the sign-in test account you used before.
    User_Name = os.environ.get("APP_USERNAME", "")
    User_Password = os.environ.get("APP_PASSWORD", "")

    def test_keep_me_signed_in_SME_14343(self, request):
        driver = request.node.driver  # Use the driver from the autouse fixture
        session_id = driver.session_id

        try:
            appium_utils = AppiumUtils()
            screenshot_folder = "screenshots"
            GeneralUtils.take_screenshot(driver, screenshot_folder)
            TestGeneric.allow_notifications(driver)
            appium_utils_instance.wait_and_click_element(driver, LoginObjects.BTN_LOGIN(),"Login")
            appium_utils_instance.wait_and_actions_sendKeys(driver, LoginObjects.INPUT_USERNAME_FIELD(), self.User_Name)
            appium_utils_instance.wait_and_actions_sendKeys(driver, LoginObjects.INPUT_PASSWORD_FIELD(),self.User_Password)
            # appium_utils.wait_and_click_element(driver, ObjectRepository.BTN_KEEP_ME_SIGNED_IN(), "KEEP_ME_SIGNED_IN")
            appium_utils_instance.click_element_position(driver, ObjectRepository.BTN_KEEP_ME_SIGNED_IN(), 0.2, 0.5)
            # checkbox = driver.find_element(By.XPATH, ObjectRepository.BTN_KEEP_ME_SIGNED_IN())
            # if PlatformType == "android":
            #     is_checked = checkbox.get_attribute('checked')
            # else:
            #     is_checked = checkbox.get_attribute('value')
            # if is_checked.lower() in ['false', '0', 'off']:
            #     checkbox.click()
            # checkbox.click()
            appium_utils.wait_for_element_and_click(driver, LoginObjects.BTN_SIGN_IN() , 10)
            appium_utils.wait_for_element(driver,LoginObjects.TXT_LANDING_MSG())
            time.sleep(3)
            appium_utils.wait_and_click_element(driver, ObjectRepository.BTN_SKIP_THIS(), "Skip This link")
            appium_utils.wait_for_element(driver, ObjectRepository.ICON_HOME())

        except Exception as e:
            print(f"An error occurred: {e}")
            Initializer.update_session_status(session_id, "failed", f"Keep me signed in test failed: {e}")
            raise  # Re-raise the exception to ensure the test fails if there's an error
        finally:
            session_url = Initializer.get_session_url(session_id)
            print(f"Test session URL: {session_url}")

