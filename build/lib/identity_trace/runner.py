import importlib
import json
from .registry import get_function_by_name, register_frame, remove_frame
from .tracer import register_trace_callback, remove_trace_callback
import os
import inspect
import uuid
import requests
import functools
import sys
import argparse



argument_parser = argparse.ArgumentParser(description='Process some arguments')
argument_parser.add_argument("--testSuiteId")
argument_parser.add_argument("--testRunId")




IDENTITY_CONFIG_FOLDER_NAME = "__identity__"

# Get the script's path
script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)


file_path = "{}/testCases/".format(IDENTITY_CONFIG_FOLDER_NAME)

if script_directory:
    file_path = script_directory + "/" + file_path

def run_test():

    print(file_path)

    args = argument_parser.parse_args()

    test_suite_id = args.testSuiteId
    test_run_id = args.testRunId

    if not test_run_id:
        raise Exception("Test run id not specified.")

    files = get_all_files_in_directory(file_path)

    if test_suite_id:
        
        if not os.path.exists(file_path + test_suite_id + ".json"):
             raise Exception("Invalid test case id {}".format(test_suite_id))

        run_test_file(test_run_id, test_suite_id, file_path + test_suite_id + ".json")

    else:
        for file in files:

            run_test_file(test_run_id, test_suite_id, file_path + file)





def run_test_file(test_run_id, test_suite_id, file_name):
    
    with open(file_name, 'r') as file:
        # Load the JSON data from the file
        data = json.load(file)
        module_name = data["functionMeta"]["moduleName"]
        if module_name == "__main__":
            dir_name = os.path.dirname(data["functionMeta"]["fileName"]) + "/"
            module_name = "{}".format(data["functionMeta"]["fileName"]).replace(dir_name, "")
            module_name = module_name.replace(".py", "")
        function_name = data["functionMeta"]["name"]

        tests = data["tests"]


        

        importlib.import_module(module_name)
        func = get_function_by_name(function_name)
        if not func:
            raise Exception("Function did not register on import.")

        
        for t in tests:
            run_function_test_case(test_run_id, test_suite_id, t, func)


def run_function_test_case(test_run_id, test_suite_id, test_case, func):

    input_to_pass = test_case["inputToPass"]
    test_case_id = test_case["id"]

    context = dict(

        _action = "copy_context",
        is_internal_execution=True,
        execution_id=id(run_test),
        description="Function Test Run",
        internal_meta=dict(
            invoked_for_test=True
        )
    )

    frame = inspect.currentframe()

    register_frame(frame, context)
    callback_id = str(uuid.uuid4())
    register_trace_callback(callback_id, functools.partial(send_trace_to_server, test_run_id, test_suite_id, test_case_id))

    try:
        kw_args = input_to_pass[-1]
        args = input_to_pass[:-1]
        
        func(*args, **kw_args)
    except Exception as e:
        print(e)
    
    remove_frame(frame)
    remove_trace_callback(callback_id)


    

def send_trace_to_server(test_run_id, test_suite_id, test_case_id, trace):

    trace["testCaseId"] = test_case_id
    trace["testSuiteId"] = test_suite_id
    trace["testRunId"] = test_run_id

    res = requests.post('http://localhost:8002/save-test-run',
                        json=trace)
    
    print(res, "this is result")
    return True


def get_all_files_in_directory(directory_path):
    # Get a list of all files and directories in the specified directory
    files_and_directories = os.listdir(directory_path)

    # Filter out directories, leaving only files
    files = [file for file in files_and_directories if os.path.isfile(os.path.join(directory_path, file))]

    return files

    