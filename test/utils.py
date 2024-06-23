
from unittest import TestCase as SuperTestCase

class TestCase(SuperTestCase):


    def assert_exception_matches(self, expected_exception, thrown_exception):
        '''
            Tests whether two exceptions are equal. Checks class type and message.
        '''

        self.assertEqual(
            str(expected_exception),
            str(thrown_exception),
            "Exception has same message"
        )

        self.assertEqual(
            isinstance(thrown_exception, type(expected_exception)),
            True,
            "Exception has same class"
        )
