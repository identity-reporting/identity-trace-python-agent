from unittest import TestCase


from identity_trace.registry import set_client_function_decorator
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

# Set the decorator before calling watch
set_client_function_decorator(mocked_decorator)



def mock_function_to_decorate():
    ...

class DecoratorTests(TestCase):


    def test_decorator_basic(self):

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
    
    def test_decorator_name(self):

        # Watch returns decorator
        decorator = watch()
        # call the decorator to check what it receives
        res = decorator(mock_function_to_decorate)
        # Name and description provided when called
        self.assertEqual(res[3], None)
        self.assertEqual(res[4], None)
    
    def test_decorator_config_override(self):

        # Watch returns decorator
        decorator = watch(config=dict(copy_output=False))
        # call the decorator to check what it receives
        res = decorator(mock_function_to_decorate)
        
        config_passed = res[5]
        self.assertEqual(config_passed["copy_output"], False)
        self.assertEqual(config_passed["copy_input"], True, "If a key in config is not overridden, it will be replaces with default")


