import pytest
from Initializer import Initializer

import pandas as pd

from sanity.test_sanity_Home import TestHome
from tests.test_Generic import TestGeneric


class TestLocal:

    @pytest.fixture(scope='module',
                    params=[4])  # Update params as needed for different devices, refer Initializer class
    def driver(self, request):
        device_index = request.param
        driver_instance = Initializer.get_driver(device_index=device_index)
        yield driver_instance
        driver_instance.quit()

    @pytest.fixture(scope='module')
    def request_fixture(self, request):
        """
        Fixture to provide the request object.
        """
        return request

    def run_test(self, request, driver):
        """
        Wrapper function to call test_product_filters with the provided request and driver.
        """
        # Create an instance of TestFilter

        test_class = TestHome()  # <<<<<<---------------- Change your test class name here

        # Mock the request.node.driver attribute
        class MockRequest:
            def __init__(self, driver):
                self.node = MockNode(driver)

        class MockNode:
            def __init__(self, driver):
                self.driver = driver

        mock_request = MockRequest(driver)

        # Call test_product_filters with the mocked request
        file_path = "QA_MEA_testdata.xlsx"
        df = pd.read_excel(file_path, sheet_name='Sanity', dtype='str')
        flag_rows = df[df['RunMode'] == 'Y']
        for index, row in flag_rows.iterrows():
            data = row.to_dict()

            # ---- your prereq block here ----
            if data.get("Login_Yes_No") == "Yes":
                TestGeneric.login_to_app(driver, data["Username"], data["Password"])

            if data.get("RemoveAllItemFromCart_Yes_No") == "Yes":
                TestGeneric.remove_all_items_from_cart(driver)

            if data.get("AddItemToCart_Yes_No") == "Yes":
                TestGeneric.search_and_add_to_cart(driver, data["Itemid"])
            # ---------------------------------
            test_class.test_ATGR_13854(mock_request, data)  # <<<<<<---------------- Change your test method name here

    def test_local(self, driver, request_fixture):
        """
        Test method for performing a successful checkout.
        """
        session_id = driver.session_id

        try:
            # Call the wrapper function to execute test_product_filters
            self.run_test(request_fixture, driver)
        except Exception as e:
            print(f"An error occurred: {e}")
            raise  # Re-raise the exception to ensure the test fails if there's an error
        finally:
            session_url = Initializer.get_session_url(session_id)
            print(f"Test session URL: {session_url}")
