import os
import requests
from appium import webdriver
from appium.options.common.base import AppiumOptions
from percy import percy_screenshot


class Initializer:
    USERNAME = os.environ.get('BROWSERSTACK_USERNAME', '')
    ACCESS_KEY = os.environ.get('BROWSERSTACK_ACCESS_KEY', '')
    # >>> CUSTOMER: CHANGE THIS app url to your own app. <<<
    # It is hardcoded and the legacy (no-SDK) path uses it directly.
    # Currently the Wikipedia sample. Your original was bs://1548e810891c53f18254d1d04527e7e3e854e442
    APP_URL = 'bs://2cb25d26a5b87168117ec49799f3cc5e51756e61'
    HUB_URL = f"https://{USERNAME}:{ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"
    BUILD_ID = ""
    SESSION_ID = ""


    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')

    @classmethod
    def get_driver(cls, device_index):

        devices = [
            {"platformVersion": "14.0", "deviceName": "Google Pixel 8 Pro"},
            {"platformVersion": "12.0", "deviceName": "Samsung Galaxy S22 Ultra"},
            {"platformVersion": "13.0", "deviceName": "OnePlus 11R"},
            {"platformVersion": "14.0", "deviceName": "Google Pixel 8"},
            {"platformVersion": "13.0", "deviceName": "Samsung Galaxy S23 Ultra"},
            {"platformVersion": "14.0", "deviceName": "Samsung Galaxy S24 Ultra"},
            {"platformVersion": "11.0", "deviceName": "Samsung Galaxy S21 Ultra"},
            {"platformVersion": "12.0", "deviceName": "Google Pixel 6 Pro"},
            {"platformVersion": "10.0", "deviceName": "Google Pixel 4 XL"},
            {"platformVersion": "11.0", "deviceName": "OnePlus 9"},
            {"platformVersion": "10.0", "deviceName": "OnePlus 8"},
            {"platformVersion": "17.0", "deviceName": "iPhone 15"}
        ]


        device = devices[device_index]
        options = AppiumOptions()

        options.load_capabilities({
            "platformName": "android", #iOS #android
            "platformVersion": device["platformVersion"],
            "deviceName": device["deviceName"],
            "appium:automationName": "UiAutomator2", #for ios 'XCUITest' and for android 'UiAutomator2'
            "appium:app": cls.APP_URL,
            "appium:noReset": "true",
            "appium:ensureWebviewsHavePages": True,
            "appium:nativeWebScreenshot": True,
            "bstack:options": {
                "source": "appiumdesktop",
                "aiAuthoring": True
            },
            "browserstack.idleTimeout": "300",
            "appium:newCommandTimeout": 3600,
            "appium:connectHardwareKeyboard": True,
            "browserstack.video": 'true',
            "appProfiling": True,
            "appium:percyOptions": {
                # enabled is default True. This can be used to disable visual testing for certain capabilities
                "enabled": False
            }
        })

        driver_instance = webdriver.Remote(cls.HUB_URL, options=options)
        percy_screenshot(driver_instance, 'App Launched')
        Initializer.SESSION_ID = driver_instance.session_id
        return driver_instance

    @classmethod
    def update_session_status(cls, session_id, status, reason):
        url = f"https://api.browserstack.com/automate/sessions/{session_id}.json"
        headers = {'Content-Type': 'application/json'}
        payload = {'status': status, 'reason': reason}

        response = requests.put(url, headers=headers, json=payload, auth=(cls.USERNAME, cls.ACCESS_KEY))
        if response.status_code == 200:
            print(f"Session status updated successfully: {url}")
        else:
            print(f"Failed to update session status: {response.status_code}")
            print(response.json())  # Print the response for debugging

    @classmethod
    def get_session_url(cls, session_id):
        return f"Dashboard: https://app-automate.browserstack.com/dashboard/v2/sessions/{session_id}"
    #
    # @classmethod
    # def take_snapshot(cls, driver):
