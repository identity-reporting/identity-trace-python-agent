import argparse

from .config import initialize_with_config_file
from .logger import logger
from .runner import execute_run_file
from .test_runner import run_tests


argument_parser = argparse.ArgumentParser(
    description='Process Run File Argument'
)
argument_parser.add_argument("--runFile")
argument_parser.add_argument("--runTests", action="store_true")
argument_parser.add_argument("--fileName")
argument_parser.add_argument("--functionName")
argument_parser.add_argument("--moduleName")
argument_parser.add_argument("--name")
argument_parser.add_argument("--reportURL")
argument_parser.add_argument("--config")
argument_parser.add_argument("--testSuiteID")


def _init():
    from .orchestration import orchestrate
    orchestrate()


def initialize(config_file_name=None):
    args = argument_parser.parse_args()

    initialize_with_config_file(
        config_file_name or args.config or None
    )

    if args.runFile:
        logger.debug(
            f"Running python code with --runFile argument ({args.runFile}).")
        return execute_run_file(args.runFile)
    elif args.runTests:
        logger.debug("Running tests with --runTests argument.")
        module_name = args.moduleName or None
        file_name = args.fileName or None
        test_suite_name = args.name or None
        report_url = args.reportURL or None
        test_suite_id = args.testSuiteID or None
        run_tests(
            module_name=module_name,
            file_name=file_name,
            test_suite_name=test_suite_name,
            report_url=report_url,
            test_suite_id=test_suite_id
        )


_init()
