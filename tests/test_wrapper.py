from unittest import mock
import uuid
from .utils import TestCase

from identity_trace.wrappers import general_wrapper, ClientExecutedFunctionTrace





class general_wrapper_test(TestCase):

    @mock.patch("identity_trace.wrappers._call_callback")
    def test_copies_info_to_trace(self, call_callback_mock):
        '''
            test whether the wrapper copies module information and other metadata to 
            client function trace
        '''

        module_name = str(uuid.uuid4())
        package_name = str(uuid.uuid4())
        file_name = str(uuid.uuid4())
        function_name = str(uuid.uuid4())
        function_description = str(uuid.uuid4())
        function_specific_config = dict()
        decorated_client_function = mock.Mock()
        decorated_client_function.return_value = uuid.uuid4()

        wrapper = general_wrapper(
            module_name,
            package_name,
            file_name,
            function_name,
            function_description,
            function_specific_config,
            decorated_client_function
        )

        res = wrapper()
        self.assertEqual(res, decorated_client_function.return_value)

        trace = call_callback_mock.call_args_list[-1][0][2]
        self.assertEqual(trace.module_name, module_name)
        self.assertEqual(trace.package_name, package_name)
        self.assertEqual(trace.file_name, file_name)
        self.assertEqual(trace.name, function_name)
        self.assertEqual(trace.description, function_description)
        self.assertEqual(trace.executed_successfully, True)
        self.assertEqual(
            trace.start_time > 0, True
        )
        self.assertEqual(
            trace.end_time > 0, True
        )
        self.assertEqual(
            trace.end_time >= trace.start_time, True
        )
    

    @mock.patch("identity_trace.wrappers._call_callback")
    def test_throws_error(self, call_callback_mock):
        '''
            test if the client function throws error then it should just throw the error as it is
        '''

        
        decorated_client_function = mock.Mock()
        mocked_error = Exception(str(uuid.uuid4()))
        decorated_client_function.side_effect = mocked_error

        wrapper = get_wrapper(decorated_client_function)

        with self.assertRaises(Exception) as exception:
            wrapper()
        
        self.assert_exception_matches(
            mocked_error,
            exception.exception
        )
        trace = call_callback_mock.call_args_list[-1][0][2]
        self.assertEqual(trace.executed_successfully, False)
        self.assertEqual(trace.error, str(mocked_error))
    
    
    def calls_client_function(self):
        '''
            calls client function with appropriate input
        '''

        
        decorated_client_function = mock.Mock()

        wrapper = get_wrapper(decorated_client_function)

        wrapper()
        decorated_client_function.assert_called_with()

        wrapper(10)
        decorated_client_function.assert_called_with(10)

        wrapper(10, some=10)
        decorated_client_function.assert_called_with(10, some=10)

        wrapper(some=10)
        decorated_client_function.assert_called_with(some=10)
    
    @mock.patch("identity_trace.wrappers.get_client_function_runner")
    def calls_client_function_runner_if_exists(self, get_client_function_runner_mock):
        '''
            If client function runner is registered, wrapper should call the runner
            with required data
        '''

        decorated_client_function = mock.Mock()

        runner_mock = mock.Mock()
        get_client_function_runner_mock.return_value = runner_mock
        runner_mock.return_value = uuid.uuid4()

        wrapper = get_wrapper(decorated_client_function)

        res = wrapper(10, some=10)

        runner_mock.assert_called_once()
        self.assertEqual(isinstance(runner_mock.call_args[0][0], ClientExecutedFunctionTrace), True)
        self.assertEqual(runner_mock.call_args[0][1], decorated_client_function)
        self.assertEqual(runner_mock.call_args[0][2], 10)
        self.assertEqual(runner_mock.call_args[1], dict(some=10))
        self.assertEqual(res, runner_mock.return_value)

        mocked_error = Exception(str(uuid.uuid4()))
        runner_mock.side_effect = mocked_error

        with self.assertRaises(Exception) as exception:
            wrapper()
        
        self.assert_exception_matches(mocked_error, exception.exception)

    @mock.patch("identity_trace.wrappers.get_tracer_callback")
    @mock.patch("identity_trace.wrappers._call_callback")
    def calls_tracer_callbacks(self, call_callback_mock, get_tracer_callback_mock):
        '''
            Tests wrapper should call tracer callback before calling client function, 
            after calling client function.
        '''

        decorated_client_function = mock.Mock()
        decorated_client_function.return_value = uuid.uuid4()

        function_specific_config = uuid.uuid4()

        wrapper = get_wrapper(decorated_client_function, function_specific_config)
        wrapper(10, some=10)

        # First tracer callback before calling client function
        self.assertEqual(
            get_tracer_callback_mock.call_args_list[0][0][0],
            "client_executed_function_preprocess"
        )
        self.assertEqual(
            call_callback_mock.call_args_list[0][0][0],
            get_tracer_callback_mock.return_value
        )
        self.assertEqual(
            call_callback_mock.call_args_list[0][0][1],
            function_specific_config
        )
        self.assertEqual(
            isinstance(call_callback_mock.call_args_list[0][0][2], ClientExecutedFunctionTrace),
            True
        )
        self.assertEqual(
            call_callback_mock.call_args_list[0][0][4],
            [10, dict(some=10)]
        )
        self.assertEqual(len(call_callback_mock.call_args_list[0][0]), 5)

        # Second tracer callback after calling client function
        self.assertEqual(
            get_tracer_callback_mock.call_args_list[1][0][0],
            "client_executed_function_postprocess"
        )
        self.assertEqual(
            call_callback_mock.call_args_list[1][0][0],
            get_tracer_callback_mock.return_value
        )
        self.assertEqual(
            call_callback_mock.call_args_list[1][0][1],
            function_specific_config
        )
        self.assertEqual(
            isinstance(call_callback_mock.call_args_list[1][0][2], ClientExecutedFunctionTrace),
            True
        )
        self.assertEqual(
            call_callback_mock.call_args_list[1][0][4],
            decorated_client_function.return_value
        )
        self.assertEqual(len(call_callback_mock.call_args_list[1][0]), 5)

        # Third tracer callback after calling client function
        self.assertEqual(
            get_tracer_callback_mock.call_args_list[2][0][0],
            "client_executed_function_finish"
        )
        self.assertEqual(
            call_callback_mock.call_args_list[2][0][0],
            get_tracer_callback_mock.return_value
        )
        self.assertEqual(
            call_callback_mock.call_args_list[2][0][1],
            function_specific_config
        )
        self.assertEqual(
            isinstance(call_callback_mock.call_args_list[2][0][2], ClientExecutedFunctionTrace),
            True
        )
        self.assertEqual(len(call_callback_mock.call_args_list[2][0]), 4)



def get_wrapper(decorated_client_function = None, function_specific_config = None):

    module_name = str(uuid.uuid4())
    package_name = str(uuid.uuid4())
    file_name = str(uuid.uuid4())
    function_name = str(uuid.uuid4())
    function_description = str(uuid.uuid4())
    function_specific_config = function_specific_config or dict()

    wrapper = general_wrapper(
        module_name,
        package_name,
        file_name,
        function_name,
        function_description,
        function_specific_config,
        decorated_client_function
    )

    return wrapper

general_wrapper_test().calls_tracer_callbacks()