from uuid import uuid4
import requests

from .logger import logger
from .utils import read_json_file_from_project_root
from .matcher import matchExecutionWithTestConfig, TestRunForTestSuite
from .runner import run_function_from_run_file


def run_tests(
        test_suite_id = None,
        module_name=None,
        file_name=None,
        test_suite_name=None,
        report_url=None
):

    run_file_path = get_tests_directory()

    test_suite_index = read_json_file_from_project_root(
        f"{run_file_path}/index.json"
    )

    passed_count = 0
    failed_count = 0

    for test_suite_index_entry in test_suite_index:

        skip_test_suite = False

        if test_suite_id and test_suite_index_entry[0] != test_suite_id:
            skip_test_suite = True
        elif module_name and not (module_name in test_suite_index_entry[2]):
            skip_test_suite = True
        elif file_name and not (file_name in test_suite_index_entry[3]):
            skip_test_suite = True

        elif test_suite_name and not (test_suite_name in test_suite_index_entry[1]):
            skip_test_suite = True

        if not skip_test_suite:

            test_suite_json = read_json_file_from_project_root(
                f"{run_file_path}/{test_suite_index_entry[0]}.json"
            )

            matcherResult = run_test_from_test_suite_json(test_suite_json)

            if matcherResult.successful:
                passed_count = passed_count + 1
            else:
                failed_count = failed_count + 1

            import time
            # Start the timer
            start_time = time.time()

            if report_url:
                send_test_report_to_url(report_url, matcherResult)

            # Stop the timer
            end_time = time.time()

            # Calculate the execution time
            execution_time = end_time - start_time
            logger.log((
                f"{matcherResult.testCaseName} {execution_time}ms. "
                f"{'Passed.' if matcherResult.successful else 'Failed.'}"
            ))
        else:
            logger.log(f"{test_suite_index_entry[1]} filtered out.")

    logger.log(f"{failed_count} Failed, {passed_count} Passed")
    if not failed_count:
        logger.log("OK.")


def run_test_from_test_suite_json(test_suite_json):

    logger.log(f"Running test {test_suite_json['name']}.")

    for test_case in test_suite_json["tests"]:

        mocks = dict()

        def visit(config):

            if config.get("isMocked", None):
                module_name = config["functionMeta"]["moduleName"]
                function_name = config["functionMeta"]["name"]
                key = f"{module_name}:{function_name}"

                if not mocks.get(key):
                    mocks[key] = dict()

                mocks[key][config["functionCallCount"]] = dict(
                    errorToThrow=config.get(
                        "mockedErrorMessage", None),
                    output=config.get("mockedOutput", None),
                )
            else:
                for child in config["children"]:
                    visit(child)

        # create mocks
        visit(test_case["config"])

        function_to_run = dict(
            function_meta=dict(
                module_name=test_case["config"]["functionMeta"]["moduleName"],
                file_name=test_case["config"]["functionMeta"]["fileName"],
                function_name=test_case["config"]["functionMeta"]["name"],
            ),
            execution_id=get_execution_id_for_test_case(),
            input_to_pass=test_case["inputToPass"],
            action="test_run",
            context=dict(
                mocks=mocks,
                test_run=dict(
                    testSuiteID=test_suite_json["id"],
                    testCaseID=test_case["id"]
                )
            )
        )
        try:
            trace_instance = run_function_from_run_file(
                function_to_run
            )
            test_case["executedFunction"] = trace_instance.serialize()
        except Exception as e:
            test_case["error"] = str(e)

    matcherResult = matchExecutionWithTestConfig(TestRunForTestSuite(
        name=test_suite_json["name"],
        description=test_suite_json["description"],
        functionMeta=test_suite_json["functionMeta"],
        testSuiteID=test_suite_json["id"],
        tests=test_suite_json["tests"]
    ))

    return matcherResult

def get_execution_id_for_test_case():
    return str(uuid4())

def send_test_report_to_url(report_url, matcherResult):
    try:
        logger.debug(
            f"Sending test result to endpoint {report_url}.")
        res = requests.post(
            report_url, json=matcherResult.serialize(), timeout=0.001)
        res.raise_for_status()

    except Exception as e:
        logger.error(
            f"Failed to send test result to {report_url}. "
            f"{e}"
        )



def get_tests_directory():
    user_settings = read_json_file_from_project_root("identity_config.json")
    return user_settings.get("tests_directory", "tests")