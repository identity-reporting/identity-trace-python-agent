import uuid
from unittest import mock
from utils import TestCase
from identity_trace.test_run import client_function_runner
from identity_trace.wrappers import ClientExecutedFunctionTrace



class client_function_runner_tests(TestCase):


    def test_returns_mock_output_if_present(self):
        '''
            Test if mock is present, then runner should return mocked output
        '''

        mock_output = str(uuid.uuid4())

        mock_config = dict(
            context = dict(
                test_run = dict(
                    mocks = {
                        "some_module:some_func": {
                            "1" : {
                                "output": mock_output
                            }
                        }
                    }
                )
            )
        )

        mock_trace = ClientExecutedFunctionTrace()
        mock_trace.module_name = "some_module"
        mock_trace.name = "some_func"
        res = client_function_runner(
            mock_config,
            mock_trace,
            None
        )

        self.assertEqual(res, mock_output, "Should return mocked output.")
    

    def test_mocked_error(self):
        '''
            Test if mock is present, then runner should throw mocked error
        '''

        mocked_error = str(uuid.uuid4())

        mock_config = dict(
            context = dict(
                test_run = dict(
                    mocks = {
                        "some_module:some_func": {
                            "1" : {
                                "errorToThrow": mocked_error
                            }
                        }
                    }
                )
            )
        )

        mock_trace = ClientExecutedFunctionTrace()
        mock_trace.module_name = "some_module"
        mock_trace.name = "some_func"
        with self.assertRaises(Exception) as exception:

            client_function_runner(
                mock_config,
                mock_trace,
                None
            )

        self.assert_exception_matches(
            Exception(mocked_error),
            exception.exception,
            "Throws mocked exception"
        )
    

    def test_calls_client_function_if_mock_not_present(self):
        '''
            Test if mock is not present, then runner should call the client function with
            provided args
        '''

        mocked_client_output = str(uuid.uuid4())

        mocked_client_function = mock.Mock()
        mocked_client_function.return_value = mocked_client_output


        mock_trace = ClientExecutedFunctionTrace()
        mock_trace.module_name = "some_module"
        mock_trace.name = "some_func"

        mock_config = dict(
            context = dict(
                test_run = dict(
                    mocks = {
                        "some_module:some_unknown_func": {
                            "1" : {
                                "errorToThrow": "somme"
                            }
                        }
                    }
                )
            )
        )

        # calls client function with no args
        res = client_function_runner(
            mock_config,
            mock_trace,
            mocked_client_function
        )

        self.assertEqual(res, mocked_client_output)
        mocked_client_function.assert_called_once_with()

        # calls client function with positional args
        res = client_function_runner(
            mock_config,
            mock_trace,
            mocked_client_function,
            10
        )

        self.assertEqual(res, mocked_client_output)
        mocked_client_function.assert_called_with(10)

        # calls client function with positional and named args
        res = client_function_runner(
            mock_config,
            mock_trace,
            mocked_client_function,
            10, some=10
        )

        self.assertEqual(res, mocked_client_output)
        mocked_client_function.assert_called_with(10, some=10)
        

    def test_mocks_correct_function_call_number(self):

        mocked_client_output = str(uuid.uuid4())

        def mocked_client_function(*args, **kwargs):
            return mocked_client_output
        
        mock_output = str(uuid.uuid4())

        mock_config = dict(
            context = dict(
                test_run = dict(
                    mocks = {
                        "some_module:some_func": {
                            "3" : {
                                "output": mock_output
                            }
                        }
                    }
                )
            )
        )

        mock_trace = ClientExecutedFunctionTrace()
        mock_trace.module_name = "some_module"
        mock_trace.name = "some_func"
        res = client_function_runner(
            mock_config,
            mock_trace,
            mocked_client_function
        )
        self.assertEqual(res, mocked_client_output, "Should run client function output for first call")

        res = client_function_runner(
            mock_config,
            mock_trace,
            mocked_client_function
        )
        self.assertEqual(res, mocked_client_output, "Should run client function output for second call")

        res = client_function_runner(
            mock_config,
            mock_trace,
            mocked_client_function
        )
        self.assertEqual(res, mock_output, "Should run mocked output for third call")

        



client_function_runner_tests().test_calls_client_function_if_mock_not_present()