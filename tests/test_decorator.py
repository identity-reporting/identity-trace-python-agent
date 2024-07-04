from unittest.mock import patch

from .utils import TestCase
from identity_trace.constants import DEFAULT_FUNCTION_SPECIFIC_CONFIG
from identity_trace.decorator import watch




def mocked_decorator(
    module_name,
    package_name,
    file_name,
    name, # Function name
    description, # Function description
    function_specific_config, # Config set by user
    decorated_client_function
):
    return [
        module_name,
        package_name,
        file_name,
        name, # Function name
        description, # Function description
        function_specific_config, # Config set by user
        decorated_client_function
    ]




def mock_function_to_decorate():
    ...

class DecoratorTests(TestCase):


    @patch("identity_trace.decorator.get_client_function_decorator")
    def test_decorator_basic(self, get_client_function_decorator_mock):

        get_client_function_decorator_mock.return_value = mocked_decorator
        # Watch returns decorator
        decorator = watch(name="some name", description="some desc")

        # call the decorator to check what it receives
        res = decorator(mock_function_to_decorate)

        self.assertEqual(
            isinstance(res, list), True, "Our mocked decorator returns a list"
        )
        # Module name
        self.assertEqual(res[0], __name__)

        # Package name
        self.assertEqual(res[1], __package__)

        # File name
        self.assertEqual(res[2], __file__)

        # Name and description provided when called
        self.assertEqual(res[3], "some name")
        self.assertEqual(res[4], "some desc")

        # If we dont provide config, it should match default config
        self.assertEqual(res[5], DEFAULT_FUNCTION_SPECIFIC_CONFIG)

        # Function to decorate
        self.assertEqual(res[6], mock_function_to_decorate)

        get_client_function_decorator_mock.assert_called_once_with()
    
    @patch("identity_trace.decorator.get_client_function_decorator")
    def test_decorator_name(self, get_client_function_decorator_mock):

        get_client_function_decorator_mock.return_value = mocked_decorator

        # Watch returns decorator
        decorator = watch()
        # call the decorator to check what it receives
        res = decorator(mock_function_to_decorate)
        # Name and description provided when called
        self.assertEqual(res[3], None)
        self.assertEqual(res[4], None)
    
    @patch("identity_trace.decorator.get_client_function_decorator")
    def test_decorator_config_override(self, get_client_function_decorator_mock):

        get_client_function_decorator_mock.return_value = mocked_decorator

        # Watch returns decorator
        decorator = watch(config=dict(copy_output=False))
        # call the decorator to check what it receives
        res = decorator(mock_function_to_decorate)
        
        config_passed = res[5]
        self.assertEqual(config_passed["copy_output"], False)
        self.assertEqual(config_passed["copy_input"], True, "If a key in config is not overridden, it will be replaces with default")


