
from unittest.mock import patch
from unittest import mock
import uuid


from identity_trace.runner import (
    run_function_from_run_file,
    run_function_by_meta,
    record_function_run_trace,
    run_function_by_code,
    FUNCTION_TRACE_MAP,
    record_function_run_trace,
    Namespaces,
    client_function_runner
)

from .utils import TestCase


class Empty():
    ...


class run_function_from_run_file_tests(TestCase):

    @patch("identity_trace.runner.delete_cache_value")
    @patch("identity_trace.runner.set_cache_value")
    @patch("identity_trace.runner.run_function_by_meta")
    def test_calls_run_function_by_meta(
        self, run_function_by_meta_mock, set_cache_value_mock, delete_cache_value_mock
    ):

        execution_id = str(uuid.uuid4())
        mock_config = dict(
            execution_id=execution_id,
            action="my_action",
            function_meta=dict(some=1)
        )

        # Mock function execution trace by execution id
        FUNCTION_TRACE_MAP[execution_id] = True

        run_function_from_run_file(
            function_config=mock_config
        )

        set_cache_value_mock.assert_called_once_with(
            Namespaces.client_function_callbacks, "runner", client_function_runner
        )
        delete_cache_value_mock.assert_called_once_with(
            Namespaces.client_function_callbacks, "runner"
        )
        run_function_by_meta_mock.assert_called_once_with(mock_config)

    @patch("identity_trace.runner.delete_cache_value")
    @patch("identity_trace.runner.set_cache_value")
    @patch("identity_trace.runner.run_function_by_code")
    def test_calls_run_function_by_code_when_code_is_present(
        self, run_function_by_code_mock, set_cache_value_mock, delete_cache_value_mock
    ):

        execution_id = str(uuid.uuid4())
        mock_config = dict(
            execution_id=execution_id,
            action="my_action",
            code="some code"
        )

        # Mock function execution trace by execution id
        FUNCTION_TRACE_MAP[execution_id] = True

        run_function_from_run_file(
            function_config=mock_config
        )

        set_cache_value_mock.assert_called_once_with(
            Namespaces.client_function_callbacks, "runner", client_function_runner
        )
        delete_cache_value_mock.assert_called_once_with(
            Namespaces.client_function_callbacks, "runner"
        )
        run_function_by_code_mock.assert_called_once_with(mock_config)

    @patch("identity_trace.runner.delete_cache_value")
    @patch("identity_trace.runner.set_cache_value")
    @patch("identity_trace.runner.run_function_by_meta")
    @patch("identity_trace.runner.run_function_by_code")
    def test_raises_exception_when_meta_and_code_not_present(
        self, run_function_by_code_mock, run_function_by_meta_mock, set_cache_value_mock,
        delete_cache_value_mock
    ):

        execution_id = str(uuid.uuid4())
        mock_config = dict(
            execution_id=execution_id,
            action="my_action",
        )

        with self.assertRaises(Exception) as exception:
            run_function_from_run_file(
                function_config=mock_config
            )

        self.assertEqual(str(exception.exception), str(
            Exception(f"Invalid function config {mock_config}.")))
        set_cache_value_mock.assert_called_once_with(
            Namespaces.client_function_callbacks, "runner", client_function_runner
        )
        delete_cache_value_mock.assert_called_once_with(
            Namespaces.client_function_callbacks, "runner"
        )
        run_function_by_code_mock.assert_not_called()
        run_function_by_meta_mock.assert_not_called()

    @patch("identity_trace.runner.delete_cache_value")
    @patch("identity_trace.runner.set_cache_value")
    @patch("identity_trace.runner.run_function_by_code")
    def test_throws_error_when_function_is_not_traced(
        self, run_function_by_code_mock, set_cache_value_mock, delete_cache_value_mock
    ):

        execution_id = str(uuid.uuid4())
        mock_config = dict(
            execution_id=execution_id,
            action="my_action",
            code="some code"
        )

        with self.assertRaises(Exception) as exception:
            run_function_from_run_file(
                function_config=mock_config
            )

        self.assertEqual(
            str(exception.exception),
            str(Exception("Function got executed but did not get traced."))
        )

    @patch("identity_trace.runner.delete_cache_value")
    @patch("identity_trace.runner.set_cache_value")
    @patch("identity_trace.runner.run_function_by_code")
    def test_returns_trace_instance(
        self, run_function_by_code_mock, set_cache_value_mock, delete_cache_value_mock
    ):

        execution_id = str(uuid.uuid4())
        mock_config = dict(
            execution_id=execution_id,
            action="my_action",
            code="some code"
        )

        return_instance = str(uuid.uuid4())
        # Mock function trace
        FUNCTION_TRACE_MAP[execution_id] = return_instance

        res = run_function_from_run_file(
            function_config=mock_config
        )

        self.assertEqual(
            res, return_instance
        )

    @patch("identity_trace.runner.delete_cache_value")
    @patch("identity_trace.runner.set_cache_value")
    @patch("identity_trace.runner.run_function_by_code")
    def test_removes_trace_entry_from_map(
        self, run_function_by_code_mock, set_cache_value_mock, delete_cache_value_mock
    ):

        execution_id = str(uuid.uuid4())
        mock_config = dict(
            execution_id=execution_id,
            action="my_action",
            code="some code"
        )

        # Mock function trace
        FUNCTION_TRACE_MAP[execution_id] = True

        run_function_from_run_file(
            function_config=mock_config
        )

        self.assertEqual(FUNCTION_TRACE_MAP.get(execution_id, None), None)


class run_function_by_meta_tests(TestCase):

    @patch("importlib.import_module")
    def test_imports_module_name(self, import_module_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            function_meta=dict(
                module_name="some_module",
                file_name="some_file_name",
                function_name="some_function"
            ),
            input_to_pass=[{}],
            execution_id=execution_id
        )

        def mock_function(*args, **kwargs):
            ...
        return_value = Empty()
        return_value.some_function = mock_function
        import_module_mock.return_value = return_value
        record_function_run_trace(execution_id)

        run_function_by_meta(mock_function_config)

        import_module_mock.assert_called_once_with(
            mock_function_config["function_meta"]["module_name"])

    @patch("importlib.import_module")
    def test_filename_as_main_module_for_main_module(self, import_module_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            function_meta=dict(
                module_name="__main__",
                file_name="some_file_name",
                function_name="some_function"
            ),
            input_to_pass=[{}],
            execution_id=execution_id
        )

        def mock_function(*args, **kwargs):
            ...
        return_value = Empty()
        return_value.some_function = mock_function
        import_module_mock.return_value = return_value
        record_function_run_trace(execution_id)

        run_function_by_meta(mock_function_config)

        import_module_mock.assert_called_once_with(
            mock_function_config["function_meta"]["file_name"])

    @patch("importlib.import_module")
    def test_module_import_error(self, import_module_mock):

        mock_function_config = dict(
            function_meta=dict(
                module_name="some_module",
                file_name="some_file_name",
                function_name="some_function"
            ),
            input_to_pass=[{}],

        )

        def mock_function(*args, **kwargs):
            raise Exception("some error")

        import_module_mock.side_effect = mock_function

        with self.assertRaises(Exception) as exception:
            run_function_by_meta(mock_function_config)

        self.assert_exception_matches(
            Exception((
                f"Could not import module some_module.\n"
                f"Original Module: some_module\n"
                f"File Name: some_file_name\n"
                f"Error: some error"
            )),
            exception.exception
        )

    @patch("importlib.import_module")
    def test_function_not_found_error(self, import_module_mock):

        mock_function_config = dict(
            function_meta=dict(
                module_name="some_module",
                file_name="some_file_name",
                function_name="some_function"
            ),
            input_to_pass=[{}],

        )

        return_value = Empty()
        import_module_mock.return_value = return_value

        with self.assertRaises(Exception) as exception:
            run_function_by_meta(mock_function_config)

        self.assert_exception_matches(
            Exception((
                f"Could not get function (some_function) by name from the registry. "
                f"Importing some_module should have registered it. "
                f"Make sure that some_function exists in some_file_name."
            )),
            exception.exception
        )

    @patch("importlib.import_module")
    def test_call_to_function(self, import_module_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            function_meta=dict(
                module_name="some_module",
                file_name="some_file_name",
                function_name="some_function"
            ),
            execution_id=execution_id,
            input_to_pass=[{}],

        )

        mocked_function_to_run = mock.Mock()

        return_value = Empty()
        return_value.some_function = mocked_function_to_run

        import_module_mock.return_value = return_value

        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_meta(mock_function_config)

        # No args
        mocked_function_to_run.assert_called_once_with()

        # Positional args with named args
        # mocked_function_to_run(1, 2, some=10)
        mock_function_config["input_to_pass"] = [1, 2, dict(some=10)]
        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_meta(mock_function_config)
        mocked_function_to_run.assert_called_with(1, 2, some=10)

        # named args only
        # mocked_function_to_run(some=10)
        mock_function_config["input_to_pass"] = [dict(some=10)]
        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_meta(mock_function_config)
        mocked_function_to_run.assert_called_with(some=10)

        # Positional args with named args
        # mocked_function_to_run(dict(some=12), some=10)
        mock_function_config["input_to_pass"] = [dict(some=12), dict(some=10)]
        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_meta(mock_function_config)
        mocked_function_to_run.assert_called_with(dict(some=12), some=10)

        # Positional args only
        mock_function_config["input_to_pass"] = [1, 2, dict()]
        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_meta(mock_function_config)
        mocked_function_to_run.assert_called_with(1, 2)

    @patch("importlib.import_module")
    def test_function_throws_error(self, import_module_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            function_meta=dict(
                module_name="some_module",
                file_name="some_file_name",
                function_name="some_function"
            ),
            execution_id=execution_id,
            input_to_pass=[{}],

        )

        def mocked_function_to_run(*args, **kwargs):
            raise Exception("some exception")

        return_value = Empty()
        return_value.some_function = mocked_function_to_run

        import_module_mock.return_value = return_value

        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_meta(mock_function_config)

    @patch("importlib.import_module")
    def test_function_throws_error(self, import_module_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            function_meta=dict(
                module_name="some_module",
                file_name="some_file_name",
                function_name="some_function"
            ),
            execution_id=execution_id,
            input_to_pass=[{}],

        )

        mock_function_to_run = mock.Mock()
        mock_function_to_run.side_effect = Exception("some exception")

        return_value = Empty()
        return_value.some_function = mock_function_to_run

        import_module_mock.return_value = return_value

        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_meta(mock_function_config)
        mock_function_to_run.assert_called_once_with()

    @patch("importlib.import_module")
    def test_function_throws_error_with_no_trace_recorded(self, import_module_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            function_meta=dict(
                module_name="some_module",
                file_name="some_file_name",
                function_name="some_function"
            ),
            execution_id=execution_id,
            input_to_pass=[{}],

        )

        mock_function_to_run = mock.Mock()
        mock_function_to_run.side_effect = Exception("some exception")

        return_value = Empty()
        return_value.some_function = mock_function_to_run

        import_module_mock.return_value = return_value

        with self.assertRaises(Exception) as exception:
            run_function_by_meta(mock_function_config)

        self.assert_exception_matches(
            Exception("some exception"), exception.exception)

    @patch("importlib.import_module")
    def test_function_run_with_no_trace_recorded(self, import_module_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            function_meta=dict(
                module_name="some_module",
                file_name="some_file_name",
                function_name="some_function"
            ),
            execution_id=execution_id,
            input_to_pass=[{}],

        )

        mock_function_to_run = mock.Mock()

        return_value = Empty()
        return_value.some_function = mock_function_to_run

        import_module_mock.return_value = return_value

        with self.assertRaises(Exception) as exception:
            run_function_by_meta(mock_function_config)

        self.assert_exception_matches(Exception((
            f"No trace recorded for the execution of some_function. "
            f"This can happen if the function is not decorated using @watch. "
            f"It can also happen because of internal error."
        )), exception.exception)


class run_function_by_code_tests(TestCase):

    @patch("identity_trace.runner.execute_code_string")
    def test_runs_code(self, execute_code_string_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            code="some_code",
            execution_id=execution_id,
            input_to_pass=[{}],

        )

        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_code(mock_function_config)
        execute_code_string_mock.assert_called_once_with(
            mock_function_config["code"])

    @patch("identity_trace.runner.execute_code_string")
    def test_code_exec_failure(self, execute_code_string_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            code="some_code",
            execution_id=execution_id,
            input_to_pass=[{}],

        )

        expected_exception = Exception(
            "invalid syntax error"
        )
        execute_code_string_mock.side_effect = expected_exception

        # When the code errors out without trace record
        with self.assertRaises(Exception) as exception:
            run_function_by_code(mock_function_config)

        self.assert_exception_matches(
            expected_exception,
            exception.exception
        )

        # But if the execution trace is recorded
        # it should not raise any error since

        # Fake execution trace record
        record_function_run_trace(execution_id)
        run_function_by_code(mock_function_config)
        execute_code_string_mock.assert_called_with("some_code")

    @patch("identity_trace.runner.execute_code_string")
    def test_code_exec_no_trace(self, execute_code_string_mock):

        execution_id = str(uuid.uuid4())
        mock_function_config = dict(
            code="some_code",
            execution_id=execution_id,
            input_to_pass=[{}],

        )

        # When the code errors out without trace record
        with self.assertRaises(Exception) as exception:
            run_function_by_code(mock_function_config)

        execute_code_string_mock.assert_called_once_with("some_code")

        self.assert_exception_matches(
            Exception((
                f"No trace recorded for the execution of code. "
                f"This can happen if the function is not decorated using @watch. "
                f"It can also happen because of internal error."
            )),
            exception.exception
        )
