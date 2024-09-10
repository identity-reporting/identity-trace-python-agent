from unittest.mock import patch
from .utils import TestCase

from identity_trace.matcher import (
    matchExecutionWithTestConfig, TestRunForTestSuite, TestResult, matchFunctionWithConfig,
    objectIsEqual, objectContains
)


__count__ = 0


def side_effect_returns_false_once(*args, **kwargs):
    class Res:
        ...
    res = Res()
    global __count__
    __count__ = __count__ + 1
    if __count__ == 1:
        res.successful = False
    else:
        res.successful = True

    return res


def side_effect_returns_true(*args, **kwargs):
    class Res:
        ...
    res = Res()
    res.successful = True
    return res


class test_matchExecutionWithTestConfig(TestCase):

    @patch("identity_trace.matcher.matchFunctionWithConfig")
    def test_matches_every_test_with_executed_function(self, matchFunctionWithConfig_mock):

        mock_test_run_config = TestRunForTestSuite(
            name="test_suite_1",
            description="some_desc",
            functionMeta=dict(some_meta=1),
            testSuiteID="test_suite_id_1",
            tests=[
                dict(
                    executedFunction="some_executed_function",
                    config="some_config",
                    name="test_1"
                ),
                dict(
                    executedFunction="some_executed_function_2",
                    config="some_config_2",
                    name="test_2"
                )
            ]
        )
        matchExecutionWithTestConfig(mock_test_run_config)
        self.assertEqual(
            matchFunctionWithConfig_mock.call_args_list[0][0],
            ("some_executed_function", "some_config")
        )
        self.assertEqual(
            matchFunctionWithConfig_mock.call_args_list[1][0],
            ("some_executed_function_2", "some_config_2")
        )
        self.assertEqual(matchFunctionWithConfig_mock.call_count, 2)

    @patch("identity_trace.matcher.matchFunctionWithConfig")
    def test_returns_correct_object(self, matchFunctionWithConfig_mock):

        self.maxDiff = None
        mock_test_run_config = TestRunForTestSuite(
            name="test_suite_1",
            description="some_desc",
            functionMeta=dict(some_meta=1),
            testSuiteID="test_suite_id_1",
            tests=[
                dict(
                    executedFunction="some_executed_function",
                    config="some_config",
                    name="test_1"
                ),
                dict(
                    executedFunction="some_executed_function_2",
                    config="some_config_2",
                    name="test_2"
                )
            ]
        )
        matchFunctionWithConfig_mock.side_effect = side_effect_returns_false_once

        res = matchExecutionWithTestConfig(mock_test_run_config)

        global __count__
        __count__ = 0

        test_res_1 = side_effect_returns_false_once()
        test_res_2 = side_effect_returns_false_once()

        self.assertEqual(res.testCaseName, "test_suite_1")
        self.assertEqual(res.testCaseDescription, "some_desc")
        self.assertEqual(res.functionMeta, dict(some_meta=1))
        self.assertEqual(res.testSuiteID, "test_suite_id_1")
        self.assertEqual(res.successful, False)
        self.assertEqual(len(res.result), 2)

        self.assertEqual(
            set(dict(
                expectation="test_1",
                successful=test_res_1.successful,
                error=None
            ).items()).issubset(set(res.result[0].items())),
            True
        )

        self.assertEqual(res.result[0]["result"].__dict__, test_res_1.__dict__)

        self.assertEqual(set(dict(
            expectation="test_2",
            successful=test_res_2.successful,
            error=None
        ).items()).issubset(set(res.result[1].items())), True)

        self.assertEqual(res.result[1]["result"].__dict__, test_res_2.__dict__)


class test_matchFunctionWithConfig(TestCase):

    @patch("identity_trace.matcher.objectIsEqual")
    def test_calls_object_equals_with_equals_operator(self, objectIsEqual_mock):

        mock_executed_function = dict(
            id="some_func_id",
            input="some_input",
            executedSuccessfully=True,
            error=None,
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    ioConfig=dict(
                        target="input",
                        operator="equals",
                        object="some_expected_input",
                    )
                )
            ]
        )
        matchFunctionWithConfig(mock_executed_function, mock_config)
        objectIsEqual_mock.assert_called_once_with(
            "some_expected_input",
            "some_input"
        )

    @patch("identity_trace.matcher.objectContains")
    def test_calls_object_contains(self, objectContains_mock):

        mock_executed_function = dict(
            id="some_func_id",
            input="some_input",
            executedSuccessfully=True,
            error=None,
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    ioConfig=dict(
                        target="input",
                        operator="contains",
                        object="some_expected_input",
                    )
                )
            ]
        )
        matchFunctionWithConfig(mock_executed_function, mock_config)
        objectContains_mock.assert_called_once_with(
            "some_expected_input",
            "some_input"
        )

    @patch("identity_trace.matcher.objectContains")
    def test_checks_output_in_assertion(self, objectContains_mock):

        mock_executed_function = dict(
            id="some_func_id",
            input="some_input",
            output="some_output",
            executedSuccessfully=True,
            error=None,
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    ioConfig=dict(
                        target="output",
                        operator="contains",
                        object="some_expected_input",
                    )
                )
            ]
        )
        matchFunctionWithConfig(mock_executed_function, mock_config)
        objectContains_mock.assert_called_once_with(
            "some_expected_input",
            "some_output"
        )

    @patch("identity_trace.matcher.objectContains")
    def test_fails_assertion_on_object_contains_fail(self, objectContains_mock):

        mock_executed_function = dict(
            id="some_func_id",
            input="some_input",
            output="some_output",
            executedSuccessfully=True,
            error=None,
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    ioConfig=dict(
                        target="output",
                        operator="contains",
                        object="some_expected_input",
                    )
                )
            ]
        )
        objectContains_mock.return_value = False
        res = matchFunctionWithConfig(mock_executed_function, mock_config)
        self.assertEqual(
            res.assertions[0],
            dict(
                name="some_assertion_name",
                success=False,
                failureReasons=["Output does not match the expectation."],
                ioConfig=dict(
                    target="output",
                    operator="contains",
                    object="some_expected_input",
                    receivedObject="some_output",
                    thrownError=None
                )
            )
        )

    @patch("identity_trace.matcher.objectIsEqual")
    def test_fails_assertion_on_object_equals_fail(self, objectIsEqual_mock):

        mock_executed_function = dict(
            id="some_func_id",
            input="some_input",
            output="some_output",
            executedSuccessfully=True,
            error=None,
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    ioConfig=dict(
                        target="output",
                        operator="equals",
                        object="some_expected_input",
                        thrownError=None
                    )
                )
            ]
        )
        objectIsEqual_mock.return_value = False
        res = matchFunctionWithConfig(mock_executed_function, mock_config)
        self.assertEqual(
            res.assertions[0],
            dict(
                name="some_assertion_name",
                success=False,
                failureReasons=["Output does not match the expectation."],
                ioConfig=dict(
                    target="output",
                    operator="equals",
                    object="some_expected_input",
                    receivedObject="some_output",
                    thrownError=None
                )
            )
        )

    def test_matches_error_message(self):

        mock_executed_function = dict(
            id="some_func_id",
            executedSuccessfully=False,
            error="thrown_error",
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    expectedErrorMessage=dict(
                        operator="equals",
                        message="expected_error",
                    )
                )
            ]
        )

        res = matchFunctionWithConfig(mock_executed_function, mock_config)
        self.assertEqual(
            res.assertions[0],
            dict(
                name="some_assertion_name",
                success=False,
                failureReasons=["Error message does not match."],
                expectedErrorMessage=dict(
                    operator="equals",
                    message="expected_error",
                    receivedError="thrown_error",
                    functionOutput=None
                )
            )
        )

        mock_executed_function["error"] = "expected_error"
        res = matchFunctionWithConfig(mock_executed_function, mock_config)
        self.assertEqual(
            res.assertions[0],
            dict(
                name="some_assertion_name",
                success=True,
                failureReasons=[],
                expectedErrorMessage=dict(
                    operator="equals",
                    message="expected_error",
                    receivedError="expected_error",
                    functionOutput=None
                )
            )
        )

    def test_matches_error_message_contains(self):
        self.maxDiff = None

        mock_executed_function = dict(
            id="some_func_id",
            executedSuccessfully=False,
            error="some_thrown_error_error",
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    expectedErrorMessage=dict(
                        operator="contains",
                        message="thrown_error",
                    )
                )
            ]
        )

        res = matchFunctionWithConfig(mock_executed_function, mock_config)
        self.assertEqual(
            res.assertions[0],
            dict(
                name="some_assertion_name",
                success=True,
                failureReasons=[],
                expectedErrorMessage=dict(
                    operator="contains",
                    message="thrown_error",
                    receivedError="some_thrown_error_error",
                    functionOutput=None
                )
            )
        )

        mock_executed_function["error"] = "some"
        res = matchFunctionWithConfig(mock_executed_function, mock_config)
        self.assertEqual(
            res.assertions[0],
            dict(
                name="some_assertion_name",
                success=False,
                failureReasons=[
                    'Error message does not contain "thrown_error"'],
                expectedErrorMessage=dict(
                    operator="contains",
                    message="thrown_error",
                    receivedError="some",
                    functionOutput=None
                )
            )
        )

    def test_fails_when_any_assertion_fails(self):

        mock_executed_function = dict(
            id="some_func_id",
            executedSuccessfully=False,
            error="some_thrown_error_error",
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    expectedErrorMessage=dict(
                        operator="contains",
                        message="thrown_error",
                    )
                ),
                dict(
                    name="some_assertion_name",
                    expectedErrorMessage=dict(
                        operator="contains",
                        message="1",
                    )
                )
            ]
        )

        res = matchFunctionWithConfig(mock_executed_function, mock_config)
        self.assertEqual(res.successful, False)

    def test_has_correct_output(self):

        mock_executed_function = dict(
            id="some_func_id",
            executedSuccessfully=False,
            input="some_input_passed",
            error="some_thrown_error_error",
            executionContext=dict(some=1)
        )
        mock_config = dict(
            children=[],
            functionMeta=dict(
                name="some_name_func",
            ),
            assertions=[
                dict(
                    name="some_assertion_name",
                    expectedErrorMessage=dict(
                        operator="contains",
                        message="thrown_error",
                    )
                ),
            ]
        )

        res = matchFunctionWithConfig(mock_executed_function, mock_config)
        self.assertEqual(res.successful, True)
        self.assertEqual(res.name, "some_name_func")
        self.assertEqual(res.executedSuccessfully,
                         mock_executed_function["executedSuccessfully"])
        self.assertEqual(res.thrownError, mock_executed_function["error"])
        self.assertEqual(res.executionContext,
                         mock_executed_function["executionContext"])
        self.assertEqual(res.id, mock_executed_function["id"])
        self.assertEqual(res.functionMeta, mock_executed_function)


class test_objectIsEqual(TestCase):

    def test_matches_correctly(self):

        self.assertEqual(
            objectIsEqual(
                dict(some=1, another=dict(another=1)),
                dict(some=1, another=dict(another=1))
            ),
            True
        )
        self.assertEqual(
            objectIsEqual(
                dict(some=1, another=dict(another=1)),
                dict(some=1, another=dict(another=2))
            ),
            False
        )
        self.assertEqual(
            objectIsEqual(
                dict(some=1, some1=2, another=dict(another=1)),
                dict(some=1, another=dict(another=1))
            ),
            False
        )
        self.assertEqual(
            objectIsEqual(
                dict(some=1, another=dict(another=1)),
                1
            ),
            False
        )
        self.assertEqual(
            objectIsEqual(
                1,
                1
            ),
            True
        )
        self.assertEqual(
            objectIsEqual(
                [1, 2, dict(some=1)],
                [1, 2, dict(some=1)]
            ),
            True
        )
        self.assertEqual(
            objectIsEqual(
                [1, 2, dict(some=1)],
                [1, 3, dict(some=1)]
            ),
            False
        )

        self.assertEqual(
            objectIsEqual(
                [1, 2, dict(some=1)],
                1
            ),
            False
        )


class test_objectContains(TestCase):

    def test_matches_correctly(self):

        self.assertEqual(
            objectContains(
                dict(some=1),
                dict(another=1, some=1)
            ),
            True
        )

        self.assertEqual(
            objectContains(
                dict(some=1),
                dict(another=1, some1=1)
            ),
            False
        )
        self.assertEqual(
            objectContains(
                dict(some=1),
                1
            ),
            False
        )

        self.assertEqual(
            objectContains(
                [1, 2],
                [1, 2]
            ),
            True
        )

        self.assertEqual(
            objectContains(
                [1, 2],
                [1, 3, 2]
            ),
            False
        )

        self.assertEqual(
            objectContains(
                [1, 2],
                1
            ),
            False
        )
