import importlib
import json
from .registry import get_function_by_name, register_frame, remove_frame, register_function_processor, remove_function_processor_callback
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
argument_parser.add_argument("--runFile")




IDENTITY_CONFIG_FOLDER_NAME = "__identity__"

# Get the script's path
script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)


file_path = "{}/TestCase/".format(IDENTITY_CONFIG_FOLDER_NAME)

if script_directory:
    file_path = script_directory + "/" + file_path

def run_test():

    print(file_path)

    args = argument_parser.parse_args()

    if args.runFile:
        return run_command_file(args.runFile)

    # python test.py --testSuiteId="1711758297852" --testRunId="run1"
    test_suite_id = args.testSuiteId or "1712285328831"
    test_run_id = args.testRunId or "run1"

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
            invoked_for_test=True,
            test_case_config = test_case
        )
    )

    frame = inspect.currentframe()

    register_frame(frame, context)
    callback_id = str(uuid.uuid4())
    register_trace_callback(callback_id, functools.partial(send_trace_to_server, test_run_id, test_suite_id, test_case_id))
    register_function_processor(process_function_to_be_executed(test_case))

    try:
        kw_args = input_to_pass[-1]
        args = input_to_pass[:-1]
        
        func(*args, **kw_args)
    except Exception as e:
        print(e)
    
    remove_frame(frame)
    remove_trace_callback(callback_id)
    remove_function_processor_callback()


    

def send_trace_to_server(test_run_id, test_suite_id, test_case_id, trace):

    trace["testCaseId"] = test_case_id
    trace["testSuiteId"] = test_suite_id
    trace["testRunId"] = test_run_id

    res = requests.post('http://localhost:8002/test_run/save-test-run',
                        json=trace)
    
    print(res, "this is result")
    return True


def get_all_files_in_directory(directory_path):
    # Get a list of all files and directories in the specified directory
    files_and_directories = os.listdir(directory_path)

    # Filter out directories, leaving only files
    files = [file for file in files_and_directories if os.path.isfile(os.path.join(directory_path, file))]

    return files




def run_command_file(file_id):


    file_path1 = f"{IDENTITY_CONFIG_FOLDER_NAME}/ExecutedFunction/{file_id}.json"

    if script_directory:
        file_path1 = f"{script_directory}/{file_path1}"

    print(f"Opening Run file: {file_path1}")
    file = open(file_path1, "r")

    # Read the entire contents of the file
    file_contents = file.read()
    # Close the file
    file.close()

    data = json.loads(file_contents)

    

    if data["type"] == "run_function":

        module_name = data["moduleName"]
        if module_name == "__main__":
            dir_name = os.path.dirname(data["fileName"]) + "/"
            module_name = "{}".format(data["fileName"]).replace(dir_name, "")
            module_name = module_name.replace(".py", "")
        function_name = data["name"]
        input_to_pass = data["inputToPass"]


        importlib.import_module(module_name)
        func = get_function_by_name(function_name)
        if not func:
            raise Exception("Function did not register on import.")

        context = dict(

            _action = "copy_context",
            is_internal_execution=True,
            execution_id=id(run_test),
            description="Run function with input",
            internal_meta=dict(
                invoked_for_test=True
            )
        )

        def write_trace_to_file(traces):
            data_to_write = dict()
            data_to_write.update(data)
            data_to_write["executedFunction"] = traces

            file = open(file_path1, "w")
            file.write(json.dumps(data_to_write))
            file.close()
            return True


        frame = inspect.currentframe()

        register_frame(frame, context)
        callback_id = str(uuid.uuid4())
        register_trace_callback(callback_id, write_trace_to_file)

        try:
            kw_args = input_to_pass[-1]
            args = input_to_pass[:-1]
            
            func(*args, **kw_args)
        except Exception as e:
            print(e)
        
        remove_frame(frame)
        remove_trace_callback(callback_id)
            



def process_function_to_be_executed(testCase):

    calls = dict()

    mocks = testCase["mocks"]



    def function_processor(function_trace, func):

        function_name = function_trace.name
        module_name = function_trace.module_name


        if not mocks.get(function_name, None):
            return func

        if not isinstance(mocks[function_name], dict):
            return func

        if not calls.get(function_name, None):
            calls[function_name] = 0

        
        calls[function_name] += 1

        if not mocks[function_name].get(str(calls[function_name]), None):
            return func
        
        def handler(*args, **kwargs):
            function_trace.execution_context["isMocked"] = True
            if mocks[function_name][str(calls[function_name])]["output"]:
                return mocks[function_name][str(calls[function_name])]["output"]

            if mocks[function_name][str(calls[function_name])]["error"]:
                raise Exception(mocks[function_name][str(calls[function_name])]["error"])
        

        return handler

    return function_processor

