from unittest.mock import patch
from .utils import TestCase

from identity_trace.test_runner import run_tests, run_test_from_test_suite_json, TestRunForTestSuite


def test_file_read_side_effect(file_name):
    if "/index.json" in file_name:
        return []

    return {}


class run_tests_tests(TestCase):

    @patch("identity_trace.test_runner.get_tests_directory")
    @patch("identity_trace.test_runner.read_json_file_from_project_root")
    def test_reads_index_file(self, read_json_file_from_project_root_mock, get_tests_directory_mock):
        get_tests_directory_mock.return_value = "TestCase"
        read_json_file_from_project_root_mock.return_value = []

        run_tests()
        
        read_json_file_from_project_root_mock.assert_called_once_with(
            "TestCase/index.json")

    @patch("identity_trace.test_runner.get_tests_directory")
    @patch("identity_trace.test_runner.run_test_from_test_suite_json")
    @patch("identity_trace.test_runner.read_json_file_from_project_root")
    def test_filters_by_module_name(
        self, read_json_file_from_project_root_mock, run_test_from_test_suite_json_mock,
        get_tests_directory_mock
    ):
        '''
            Check whether the filter by module name works
        '''
        get_tests_directory_mock.return_value = "TestCase"

        read_json_file_from_project_root_mock.return_value = [
            ["some_id", "name", "module1", "filename"],
            ["some_id", "name", "module1", "filename"],
            ["some_id", "name", "module1", "filename"],
            ["some_id4", "name", "anotherMod", "filename"],
        ]

        class Matcher:
            ...
        matcher_result = Matcher()
        matcher_result.successful = True
        matcher_result.testCaseName = "name"
        run_test_from_test_suite_json_mock.return_value = matcher_result

        run_tests(
            module_name="another"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_args_list[0][0][0],
            "TestCase/index.json"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_args_list[1][0][0],
            "TestCase/some_id4.json"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_count,
            2
        )

    @patch("identity_trace.test_runner.get_tests_directory")
    @patch("identity_trace.test_runner.run_test_from_test_suite_json")
    @patch("identity_trace.test_runner.read_json_file_from_project_root")
    def test_filters_by_file_name(
        self, read_json_file_from_project_root_mock, run_test_from_test_suite_json_mock,
        get_tests_directory_mock
    ):
        '''
            Check whether the filter by file name works
        '''
        get_tests_directory_mock.return_value = "TestCase"
        read_json_file_from_project_root_mock.return_value = [
            ["some_id", "name", "module1", "filename"],
            ["some_id", "name", "module1", "filename"],
            ["some_id3", "name", "module1", "some_di"],
            ["some_id4", "name", "anotherMod", "some_fi"],
        ]

        class Matcher:
            ...
        matcher_result = Matcher()
        matcher_result.successful = True
        matcher_result.testCaseName = "name"
        run_test_from_test_suite_json_mock.return_value = matcher_result

        run_tests(
            file_name="some"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_args_list[0][0][0],
            "TestCase/index.json"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_args_list[1][0][0],
            "TestCase/some_id3.json"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_args_list[2][0][0],
            "TestCase/some_id4.json"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_count,
            3
        )

    @patch("identity_trace.test_runner.get_tests_directory")
    @patch("identity_trace.test_runner.run_test_from_test_suite_json")
    @patch("identity_trace.test_runner.read_json_file_from_project_root")
    def test_filters_by_test_suite_name(
        self, read_json_file_from_project_root_mock, run_test_from_test_suite_json_mock,
        get_tests_directory_mock
    ):
        '''
            Check whether the filter by file name works
        '''
        get_tests_directory_mock.return_value = "TestCase"
        read_json_file_from_project_root_mock.return_value = [
            ["some_id", "name1", "module1", "filename"],
            ["some_id", "name1", "module1", "filename"],
            ["some_id3", "another_name1", "module1", "some_di"],
            ["some_id4", "another_name2", "anotherMod", "some_fi"],
        ]

        class Matcher:
            ...
        matcher_result = Matcher()
        matcher_result.successful = True
        matcher_result.testCaseName = "name"
        run_test_from_test_suite_json_mock.return_value = matcher_result

        run_tests(
            test_suite_name="another"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_args_list[0][0][0],
            "TestCase/index.json"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_args_list[1][0][0],
            "TestCase/some_id3.json"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_args_list[2][0][0],
            "TestCase/some_id4.json"
        )
        self.assertEqual(
            read_json_file_from_project_root_mock.call_count,
            3
        )


class test_run_test_from_test_suite_json(TestCase):

    @patch("identity_trace.test_runner.get_execution_id_for_test_case")
    @patch("identity_trace.test_runner.matchExecutionWithTestConfig")
    @patch("identity_trace.test_runner.run_function_from_run_file")
    def test_passes_correct_meta_to_run_function(
        self, run_function_from_run_file_mock, matchExecutionWithTestConfig_mock,
        get_execution_id_for_test_case_mock
    ):

        self.maxDiff = None
        test_suite_mock = dict(
            id="test_id_1",
            name="test_suite_1",
            description="some_desc",
            functionMeta=dict(
                moduleName="module_1",
                fileName="fileName1",
                name="some"
            ),
            tests=[
                dict(
                    id="test_case_id_1",
                    config=dict(
                        functionMeta=dict(
                            moduleName="module_1",
                            fileName="fileName1",
                            name="some"
                        ),
                        children=[]
                    ),
                    inputToPass=[1, dict(some=1)]
                ),
                dict(
                    id="test_case_id_2",
                    config=dict(
                        functionMeta=dict(
                            moduleName="module_2",
                            fileName="fileName2",
                            name="some2"
                        ),
                        children=[]
                    ),
                    inputToPass=[2, dict(some2=2)]
                )
            ]
        )

        test_meta_mock = dict(
            function_meta=dict(
                module_name="module_1",
                file_name="fileName1",
                function_name="some",
            ),
            input_to_pass=[1, dict(some=1)],
            action="test_run",
            execution_id="execution_id",
            context=dict(
                mocks=dict(),
                test_run=dict(
                    testSuiteID="test_id_1",
                    testCaseID="test_case_id_1"
                )
            )
        )
        test_meta_mock2 = dict(
            function_meta=dict(
                module_name="module_2",
                file_name="fileName2",
                function_name="some2",
            ),
            input_to_pass=[2, dict(some2=2)],
            action="test_run",
            execution_id="execution_id",
            context=dict(
                mocks=dict(),
                test_run=dict(
                    testSuiteID="test_id_1",
                    testCaseID="test_case_id_2"
                )
            )
        )

        get_execution_id_for_test_case_mock.return_value = "execution_id"
        run_test_from_test_suite_json(test_suite_mock)
        self.assertEqual(
            run_function_from_run_file_mock.call_args_list[0][0][0],
            test_meta_mock
        )
        self.assertEqual(
            run_function_from_run_file_mock.call_args_list[1][0][0],
            test_meta_mock2
        )
        self.assertEqual(run_function_from_run_file_mock.call_count, 2)

        self.assertEqual(
            matchExecutionWithTestConfig_mock.call_args[0][0].__dict__,
            TestRunForTestSuite(
                name=test_suite_mock["name"],
                description=test_suite_mock["description"],
                functionMeta=test_suite_mock["functionMeta"],
                testSuiteID=test_suite_mock["id"],
                tests=test_suite_mock["tests"]
            ).__dict__
        )
        self.assertEqual(matchExecutionWithTestConfig_mock.call_count, 1)

    @patch("identity_trace.test_runner.get_execution_id_for_test_case")
    @patch("identity_trace.test_runner.matchExecutionWithTestConfig")
    @patch("identity_trace.test_runner.run_function_from_run_file")
    def test_passes_mocks(
        self, run_function_from_run_file_mock, matchExecutionWithTestConfig_mock,
        get_execution_id_for_test_case_mock
    ):

        self.maxDiff = None
        test_suite_mock = dict(
            id="test_id_1",
            name="test_suite_1",
            description="some_desc",
            functionMeta=dict(
                moduleName="module_1",
                fileName="fileName1",
                name="some"
            ),
            tests=[
                dict(
                    id="test_case_id_1",
                    config=dict(
                        functionMeta=dict(
                            moduleName="module_1",
                            fileName="fileName1",
                            name="some"
                        ),
                        children=[],
                        isMocked=True,
                        mockedErrorMessage=None,
                        mockedOutput="mocked_output_1",
                        functionCallCount=1
                    ),
                    inputToPass=[1, dict(some=1)],
                )
            ]
        )

        test_meta_mock = dict(
            function_meta=dict(
                module_name="module_1",
                file_name="fileName1",
                function_name="some",
            ),
            input_to_pass=[1, dict(some=1)],
            action="test_run",
            execution_id="execution_id",
            context=dict(
                mocks={
                    "module_1:some": {
                        1: dict(
                            errorToThrow=None,
                            output="mocked_output_1"
                        )
                    }
                },
                test_run=dict(
                    testSuiteID="test_id_1",
                    testCaseID="test_case_id_1"
                )
            )
        )

        get_execution_id_for_test_case_mock.return_value = "execution_id"
        run_test_from_test_suite_json(test_suite_mock)
        self.assertEqual(
            run_function_from_run_file_mock.call_args_list[0][0][0],
            test_meta_mock
        )
        self.assertEqual(run_function_from_run_file_mock.call_count, 1)

        self.assertEqual(
            matchExecutionWithTestConfig_mock.call_args[0][0].__dict__,
            TestRunForTestSuite(
                name=test_suite_mock["name"],
                description=test_suite_mock["description"],
                functionMeta=test_suite_mock["functionMeta"],
                testSuiteID=test_suite_mock["id"],
                tests=test_suite_mock["tests"]
            ).__dict__
        )
        self.assertEqual(matchExecutionWithTestConfig_mock.call_count, 1)

    @patch("identity_trace.test_runner.get_execution_id_for_test_case")
    @patch("identity_trace.test_runner.matchExecutionWithTestConfig")
    @patch("identity_trace.test_runner.run_function_from_run_file")
    def test_nested_mocks(
        self, run_function_from_run_file_mock, matchExecutionWithTestConfig_mock,
        get_execution_id_for_test_case_mock
    ):

        self.maxDiff = None
        test_suite_mock = dict(
            id="test_id_1",
            name="test_suite_1",
            description="some_desc",
            functionMeta=dict(
                moduleName="module_1",
                fileName="fileName1",
                name="some"
            ),
            tests=[
                dict(
                    id="test_case_id_1",
                    config=dict(
                        functionMeta=dict(
                            moduleName="module_1",
                            fileName="fileName1",
                            name="some"
                        ),
                        children=[
                            dict(
                                functionMeta=dict(
                                    moduleName="module_2",
                                    fileName="fileName2",
                                    name="som2"
                                ),
                                isMocked=True,
                                mockedErrorMessage=None,
                                mockedOutput="mocked_output_2",
                                functionCallCount=1
                            ),
                            dict(
                                functionMeta=dict(
                                    moduleName="module_3",
                                    fileName="fileName3",
                                    name="som3"
                                ),
                                isMocked=True,
                                mockedErrorMessage="Some Error",
                                mockedOutput=None,
                                functionCallCount=1
                            )
                        ],
                    ),
                    inputToPass=[1, dict(some=1)],
                )
            ]
        )

        test_meta_mock = dict(
            function_meta=dict(
                module_name="module_1",
                file_name="fileName1",
                function_name="some",
            ),
            input_to_pass=[1, dict(some=1)],
            action="test_run",
            execution_id="execution_id",
            context=dict(
                mocks={
                    "module_2:som2": {
                        1: dict(
                            errorToThrow=None,
                            output="mocked_output_2"
                        )
                    },
                    "module_3:som3": {
                        1: dict(
                            errorToThrow="Some Error",
                            output=None
                        )
                    }
                },
                test_run=dict(
                    testSuiteID="test_id_1",
                    testCaseID="test_case_id_1"
                )
            )
        )

        get_execution_id_for_test_case_mock.return_value = "execution_id"
        run_test_from_test_suite_json(test_suite_mock)
        self.assertEqual(
            run_function_from_run_file_mock.call_args_list[0][0][0],
            test_meta_mock
        )
        self.assertEqual(run_function_from_run_file_mock.call_count, 1)

        self.assertEqual(
            matchExecutionWithTestConfig_mock.call_args[0][0].__dict__,
            TestRunForTestSuite(
                name=test_suite_mock["name"],
                description=test_suite_mock["description"],
                functionMeta=test_suite_mock["functionMeta"],
                testSuiteID=test_suite_mock["id"],
                tests=test_suite_mock["tests"]
            ).__dict__
        )
        self.assertEqual(matchExecutionWithTestConfig_mock.call_count, 1)
