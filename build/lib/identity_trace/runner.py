import importlib
import json
import os
import requests
import functools
import sys
import argparse

from .registry import get_cache_value, set_cache_value, Namespaces

get_run_action = functools.partial(get_cache_value, Namespaces.run_file_action)
register_tracer_callback = functools.partial(set_cache_value, Namespaces.tracer_callbacks)


FUNCTION_TRACE_MAP = dict()

argument_parser = argparse.ArgumentParser(description='Process Run File Argument')
argument_parser.add_argument("--runFile")




# 74588c94-9eee-4a89-8742-ae455dc29359
IDENTITY_CONFIG_FOLDER_NAME = "__identity__"

# Get the script's path
script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)


file_path = "{}/TestCase/".format(IDENTITY_CONFIG_FOLDER_NAME)

if script_directory:
    file_path = script_directory + "/" + file_path

def execute_run_file():

    args = argument_parser.parse_args()

    if args.runFile:
        return _execute_run_file(args.runFile)
    


def _execute_run_file(run_file_id):
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

    try:
        file = open(run_file_path, "w")
        file.write(json.dumps(run_file_config))
        file.close()
    except Exception as e:
        raise Exception((
            f"Could not write to run file {run_file_id}\n"
            f"Error: {str(e)}"
        ))


def read_run_file_json(run_file_id):
    run_file_path = f"__identity__/__temp__/{run_file_id}.json"
    # Read the run file
    if script_directory:
        run_file_path = f"{script_directory}/{run_file_path}"

    file = None
    try:
        file = open(run_file_path, "r")
        run_file_config_string = file.read()
        file.close()
    except Exception as e:
        raise Exception((
            f"Could not read from run file. Run ID:{run_file_id}\n"
            f"Error: {str(e)}"
        ))

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
    except Exception as e:
        raise Exception((
            f"Could not import module {module_name}.\n"
            f"Original Module: {function_meta['module_name']}\n"
            f"File Name: {file_name}\n"
            f"Error: {str(e)}"
        ))

    if not function_to_run:
        raise Exception((
            f"Could not get function ({function_name}) by name from the registry. "
            f"Importing {module_name} should have registered it. "
            f"Make sure that {function_name} exists in {file_name}."
        ))

    # register tracer callback
    # register_trace_callback_for_function_run(function_config)

    thrown_exception = None

    try:
        
        kw_args = input_to_pass[-1]
        args = input_to_pass[:-1]
        
        function_to_run(*args, **kw_args)

    except Exception as e:
            # If the function was not traced, it means that function didn't even
            # execute or agent failed to run the function
            thrown_exception = e
            print(e)

    if not FUNCTION_TRACE_MAP.get(function_config["execution_id"], None):
        if thrown_exception:
                raise thrown_exception
        
        raise Exception((
            f"No trace recorded for the execution of {function_name}. "
            f"This can happen if the function is not decorated using @watch. "
            f"It can also happen because of internal error."
        ))
        
    
    del FUNCTION_TRACE_MAP[function_config["execution_id"]]
    
    
    # remove tracer callback
    # remove_trace_callback_for_function_run(function_config)


def run_function_by_code(function_config):
    '''
        Runs the user specified python code provided in config using `exec`.
        Function should be called in the user defined code.
    '''

    code_to_run = function_config.get("code", None)

    # register tracer callback
    register_trace_callback_for_function_run(function_config)

    thrown_exception = None
    try:
        execute_code_string(code_to_run)
    except Exception as e:
        
        thrown_exception = e
        print(e)

    if not FUNCTION_TRACE_MAP.get(function_config["execution_id"], None):
        if thrown_exception:
                raise thrown_exception
        
        raise Exception((
            f"No trace recorded for the execution of code. "
            f"This can happen if the function is not decorated using @watch. "
            f"It can also happen because of internal error."
        ))
        
    
    del FUNCTION_TRACE_MAP[function_config["execution_id"]]
    # finally:
    #     # remove tracer callback
    #     remove_trace_callback_for_function_run(function_config)

def execute_code_string(code_string):
    exec(code_string)

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
    
    record_function_run_trace(function_config["execution_id"])

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
            write_run_file_json(run_file_id, run_file_config)
    

def record_function_run_trace(execution_id):
    FUNCTION_TRACE_MAP[execution_id] = True

