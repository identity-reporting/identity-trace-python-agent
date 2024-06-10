import importlib
import json
import requests
from .registry import get_function_by_name, register_frame, remove_frame, register_tracer_callback
from .tracer import register_trace_callback, remove_trace_callback
import os
import inspect
import uuid
import requests
import functools
import sys
import argparse
from .registry import get_run_action
from .orchestration import orchestrate

orchestrate()

argument_parser = argparse.ArgumentParser(description='Process some arguments')
argument_parser.add_argument("--testSuiteId")
argument_parser.add_argument("--testRunId")
argument_parser.add_argument("--runFile")
argument_parser.add_argument("--runCode")




# 74588c94-9eee-4a89-8742-ae455dc29359
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

    if args.runFile or "0a9c7e94-db04-4dd4-a5ba-32326d53d152":
        return execute_run_file(args.runFile or '0a9c7e94-db04-4dd4-a5ba-32326d53d152')
    
    # if args.runCode or "74588c94-9eee-4a89-8742-ae455dc29359":
    #     return run_code(args.runCode or "74588c94-9eee-4a89-8742-ae455dc29359")

    # # python test.py --testSuiteId="1711758297852" --testRunId="run1"
    # test_suite_id = args.testSuiteId or "1712285328831"
    # test_run_id = args.testRunId or "run1"

    # if not test_run_id:
    #     raise Exception("Test run id not specified.")

    # files = get_all_files_in_directory(file_path)

    # if test_suite_id:
        
    #     if not os.path.exists(file_path + test_suite_id + ".json"):
    #          raise Exception("Invalid test case id {}".format(test_suite_id))

    #     run_test_file(test_run_id, test_suite_id, file_path + test_suite_id + ".json")

    # else:
    #     for file in files:

    #         run_test_file(test_run_id, test_suite_id, file_path + file)





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



def run_code(run_file_id):
    
    file_path1 = f"{IDENTITY_CONFIG_FOLDER_NAME}/__temp__/{run_file_id}.json"

    if script_directory:
        file_path1 = f"{script_directory}/{file_path1}"
    
    print(f"Opening Run file: {file_path1}")
    file = open(file_path1, "r")

    
    run_code_config = file.read()
    file.close()

    run_code_config = json.loads(run_code_config)

    code_to_run = run_code_config.get("code", "")

    def get_function_id(function_execution_trace):
        execution_id = function_execution_trace["data"][0]["_id"]
        file = open(file_path1, "w")
        run_code_config["executedFunction"] = execution_id
        file.write(json.dumps(run_code_config))
        file.close()
        

    callback_id = str(uuid.uuid4())
    register_trace_callback(callback_id, get_function_id)

    
    

    try:
        exec(code_to_run)
    except Exception as e:
        if not run_code_config.get("executedFunction", None):
            raise Exception(f"Failed to run code. Error: {str(e)}")
    
    remove_trace_callback(callback_id)




def execute_run_file(run_file_id):
    '''
        Reads run file, validates the JSON and run every function specified in the run file.
    '''

    run_file_config = read_run_file_json(run_file_id)

    run_functions_from_run_file_config(run_file_id, run_file_config)
    
def write_run_file_json(run_file_id, run_file_config):

    run_file_path = f"__identity__/__temp__/{run_file_id}.json"

    # Read the run file
    if script_directory:
        run_file_path = f"{script_directory}/{run_file_path}"

    file = open(run_file_path, "w")
    file.write(json.dumps(run_file_config))
    file.close()


def read_run_file_json(run_file_id):
    run_file_path = f"__identity__/__temp__/{run_file_id}.json"
    # Read the run file
    if script_directory:
        run_file_path = f"{script_directory}/{run_file_path}"

    file = open(run_file_path, "r")
    run_file_config_string = file.read()
    file.close()

    # parse json
    run_file_config = None
    try:
        run_file_config = json.loads(run_file_config_string)
    except:
        raise Exception(f"Could not parse JSON config from run file. {str(run_file_config)}")

    
    validate_run_file(run_file_config)

    return run_file_config


def run_functions_from_run_file_config(run_file_id, run_file_config):
    '''
        Executes every function specified in the run file.
    '''
    # Run each function specified in the run file
    for function_config in run_file_config["functions_to_run"]:
        run_function_from_run_file(run_file_id, run_file_config, function_config)


def run_function_from_run_file(run_file_id, run_file_config, function_config = None):
    '''
        Executed a function run configuration specified in the run file.
    '''
    function_meta = function_config.get("function_meta", None)
    
    if function_config.get("action", None):
        run_action = function_config.get("action", None)

        action_callback = get_run_action(run_action)

        if action_callback:
            action_callback(function_config, functools.partial(
                on_run_file_function_complete,
                run_file_id, run_file_config, function_config
            ))
        else:
            register_tracer_callback(
                "client_executed_function_finish",
                functools.partial(
                    on_run_file_function_complete,
                    run_file_id, run_file_config, function_config
                )
            )

    if function_meta:
        run_function_by_meta(function_config)

    else:
        run_function_by_code(function_config)
        



def run_function_by_meta(function_config):
    '''
        Imports the module or file from function_meta, gets the function from registry
        and executes it by providing the input specified in the config.
    '''

    function_meta = function_config.get("function_meta", None)
    module_name = function_meta["module_name"]
    file_name = function_meta["file_name"]
    function_name = function_meta["function_name"]
    input_to_pass = function_config["input_to_pass"]
    

    # if the module is __main__ then module name should be the file name 
    # because for this file, it will be a module
    if module_name == "__main__":

        dir_name = os.path.dirname(file_name) + "/"
        module_name = "{}".format(file_name).replace(dir_name, "")

        module_name = module_name.replace(".py", "")

    # Import the module
    try:
        module = importlib.import_module(module_name)
        function_to_run = getattr(module, function_name, None)
    except:
        raise Exception((
            f"Could not import module {module_name}.\n"
            f"Original Module: {function_meta['module_name']}\n"
            f"File Name: {file_name}"
        ))

    if not function_to_run:
        raise Exception((
            f"Could not get function ({function_name}) by name from the registry. "
            f"Importing {module_name} should have registered it. "
            f"Make sure that {function_name} exists in {file_name}."
        ))

    # register tracer callback
    register_trace_callback_for_function_run(function_config)


    try:
        
        kw_args = input_to_pass[-1]
        args = input_to_pass[:-1]
        
        function_to_run(*args, **kw_args)

    except Exception as e:
        print(e)
    
    # remove tracer callback
    remove_trace_callback_for_function_run(function_config)


def run_function_by_code(function_config):
    '''
        Runs the user specified python code provided in config using `exec`.
        Function should be called in the user defined code.
    '''

    code_to_run = function_config.get("code", None)

    # register tracer callback
    register_trace_callback_for_function_run(function_config)

    try:
        exec(code_to_run)
        
    except Exception as e:
        # TODO: detect if the tracer recorded the function execution
        # if the trace is not recorded, that means the function didn't even run
        # Which would be related to error in code
        raise e
    finally:
        # remove tracer callback
        remove_trace_callback_for_function_run(function_config)


def validate_run_file(run_file_config):
    '''
        Validates the run file configuration.
    '''
    if not run_file_config.get("functions_to_run", None):
        raise Exception("Run file does not contain any functions to run.")

    # TODO: better error handling
    if not isinstance(run_file_config.get("functions_to_run"), list):
        raise Exception("Run file does not invalid functions_to_run value. It should be a list of configurations.")

    
    return run_file_config


def register_trace_callback_for_function_run(function_config):
    ...

def remove_trace_callback_for_function_run(function_config):
    ...


def on_run_file_function_complete(
    run_file_id,
    run_file_config,
    function_config, 
    function_specific_config,
    client_executed_function_trace,
    function_frame
):
    '''
        When a function run is completed, this function will be called to handle the result.
        This will also mark the execution of the function as traced.
        Will write the executed function trace to the run file.

        @param run_file_path: File path of the run file config.
        @param run_file_config: Run file config defined in the run file.
        @param function_config: Function config for the function that is being traced. 
        This config is defined in `run_file_config['functions_to_run']` array. 
        @param function_specific_config: config defined on client function
        @param client_executed_function_trace: executed client function trace instance.
        @param function_frame: python frame of the decorator function
    '''

    if client_executed_function_trace.parent_id:
        return

    signal_endpoint = run_file_config.get("signal_endpoint", None)

    for fc in run_file_config["functions_to_run"]:
        if fc["execution_id"] == function_config["execution_id"]:
            fc["executed_function"] = client_executed_function_trace.serialize()
    
    write_run_file_json(run_file_id, run_file_config)

    if signal_endpoint:
        try:
            requests.post(
                signal_endpoint,
                json=dict(
                    run_file_id=run_file_id,
                    execution_id=function_config["execution_id"]
                )
            )
        except Exception as e:
            fc["signal_error"] = str(e)

    
    

        

    # TODO: send a signal to the calling server for function run completion
    # endpoint can be read from the function config

