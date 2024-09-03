import importlib
import inspect
import json
import os
import functools
import sys

from .registry import get_cache_value, set_cache_value, Namespaces, delete_cache_value
from .logger import logger

get_run_action = functools.partial(get_cache_value, Namespaces.run_file_action)
register_tracer_callback = functools.partial(
    set_cache_value, Namespaces.tracer_callbacks)


FUNCTION_ROOT_MAP = dict()
FUNCTION_CONFIG_MAP = dict()
FUNCTION_TRACE_MAP = dict()


# 74588c94-9eee-4a89-8742-ae455dc29359
IDENTITY_CONFIG_FOLDER_NAME = "__identity__"

# Get the script's path
script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)


file_path = "{}/TestCase/".format(IDENTITY_CONFIG_FOLDER_NAME)

if script_directory:
    file_path = script_directory + "/" + file_path


def execute_run_file(run_file_id):
    '''
        Reads run file, validates the JSON and run every function specified in the run file.
    '''
    run_file_path = f"__temp__/{run_file_id}.json"
    run_file_config = read_run_file_json(run_file_path)

    run_functions_from_run_file_config(run_file_id, run_file_config)
    write_run_file_json(run_file_path, run_file_config)


def write_run_file_json(run_file_id, run_file_config):

    run_file_path = f"__identity__/{run_file_id}"

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
    run_file_id = f"__identity__/{run_file_id}"
    # Read the run file
    if script_directory:
        run_file_id = f"{script_directory}/{run_file_id}"

    file = None
    try:
        logger.debug(f"Reading file {run_file_id}.")
        file = open(run_file_id, "r")
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
        raise Exception(
            f"Could not parse JSON config from run file. {str(run_file_config)}")

    validate_run_file(run_file_config)

    return run_file_config


def run_functions_from_run_file_config(run_file_id, run_file_config):
    '''
        Executes every function specified in the run file.
    '''
    # Run each function specified in the run file
    for function_config in run_file_config["functions_to_run"]:
        try:
            trace_instance = run_function_from_run_file(
                function_config
            )
            function_config["executed_function"] = trace_instance.serialize()
        except Exception as e:
            function_config["error"] = str(e)


def run_function_from_run_file(function_config=None):
    '''
        Executed a function run configuration specified in the run file.
    '''

    register_tracer_callback(
        "client_executed_function_finish",
        on_run_file_function_complete
    )

    # Register the current frame with config
    # Client function runner can find this config
    execution_id = function_config["execution_id"]
    current_frame = inspect.currentframe()

    FUNCTION_ROOT_MAP[current_frame] = execution_id
    FUNCTION_CONFIG_MAP[execution_id] = function_config

    set_cache_value(Namespaces.client_function_callbacks,
                    "runner", client_function_runner)

    try:
        if function_config.get("function_meta", None):
            run_function_by_meta(function_config)
        elif function_config.get("code", None):
            run_function_by_code(function_config)
        else:
            raise Exception(f"Invalid function config {function_config}.")
    finally:
        delete_cache_value(Namespaces.client_function_callbacks, "runner")

    if not FUNCTION_TRACE_MAP.get(execution_id, None):
        raise Exception("Function got executed but did not get traced.")

    function_trace_instance = FUNCTION_TRACE_MAP.get(execution_id, None)

    del FUNCTION_ROOT_MAP[current_frame]
    del FUNCTION_CONFIG_MAP[execution_id]
    del FUNCTION_TRACE_MAP[execution_id]

    return function_trace_instance


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

    logger.debug("Running function with meta.", function_meta)
    # if the module is __main__ then module name should be the file name
    # because for this file, it will be a module
    if module_name == "__main__":

        dir_name = os.path.dirname(file_name) + "/"
        module_name = "{}".format(file_name).replace(dir_name, "")

        module_name = module_name.replace(".py", "")

    # Import the module
    try:
        logger.log(f"Importing module {module_name}.")
        module = importlib.import_module(module_name)
        logger.log(f"Getting function {function_name} from {module_name}.")
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

        logger.log(f"Running function with args({args}) kwargs({kw_args}).")
        function_to_run(*args, **kw_args)

    except Exception as e:
        # If the function was not traced, it means that function didn't even
        # execute or agent failed to run the function
        thrown_exception = e
        logger.error(e)
        print(e)

    if not FUNCTION_TRACE_MAP.get(function_config["execution_id"], None):
        if thrown_exception:
            raise thrown_exception

        raise Exception((
            f"No trace recorded for the execution of {function_name}. "
            f"This can happen if the function is not decorated using @watch. "
            f"It can also happen because of internal error."
        ))

    # remove tracer callback
    # remove_trace_callback_for_function_run(function_config)


def run_function_by_code(function_config):
    '''
        Runs the user specified python code provided in config using `exec`.
        Function should be called in the user defined code.
    '''

    code_to_run = function_config.get("code", None)
    logger.debug("running function with code", code_to_run)

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

    # finally:
    #     # remove tracer callback
    #     remove_trace_callback_for_function_run(function_config)


def execute_code_string(code_string):
    exec(code_string)


def validate_run_file(run_file_config):
    '''
        Validates the run file configuration.
    '''
    return True
    if not run_file_config.get("functions_to_run", None):
        raise Exception("Run file does not contain any functions to run.")

    # TODO: better error handling
    if not isinstance(run_file_config.get("functions_to_run"), list):
        raise Exception(
            "Run file does not invalid functions_to_run value. It should be a list of configurations.")

    return run_file_config


def register_trace_callback_for_function_run(function_config):
    ...


def remove_trace_callback_for_function_run(function_config):
    ...


def on_run_file_function_complete(
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

    logger.debug((
        f"Function execution complete and recorded"
        f"for {client_executed_function_trace.name} "
        f"from {client_executed_function_trace.module_name}."
    ))

    if client_executed_function_trace.parent_id:
        return

    function_config = get_config_for_executed_client_function(
        client_executed_function_trace,
        function_frame
    )
    execution_id = function_config["execution_id"]
    FUNCTION_TRACE_MAP[execution_id] = client_executed_function_trace


__FUNCTION_CALL_COUNT_MAP__ = dict()


def client_function_runner(client_executed_function_trace, decorated_client_function,  *args, **kwargs):

    function_detail = f"{client_executed_function_trace.name} from {client_executed_function_trace.module_name}"
    logger.debug((
        f"Client function runner hit for {function_detail}"
    ))

    function_config = get_config_for_executed_client_function(
        client_executed_function_trace,
        inspect.currentframe()
    )

    client_executed_function_trace.execution_context["execution_id"] = function_config["execution_id"]

    # If function is mocked, return mock value
    context = function_config.get("context", None)
    if context and isinstance(context, dict) and context.get("mocks"):

        # Find the root function
        if not client_executed_function_trace.parent_id:
            root_function_trace = client_executed_function_trace
            client_executed_function_trace.test_run__root_function = client_executed_function_trace
        else:
            parent_function = get_cache_value(
                Namespaces.client_function_trace_by_id,
                client_executed_function_trace.parent_id
            )
            root_function_trace = parent_function.test_run__root_function
            client_executed_function_trace.test_run__root_function = root_function_trace

        # Get function call count with respect to root function
        # __FUNCTION_CALL_COUNT_MAP__[root function id] = dict (
        #    [module_name:function_name] = call count
        # )
        if not __FUNCTION_CALL_COUNT_MAP__.get(root_function_trace.id, None):
            __FUNCTION_CALL_COUNT_MAP__[root_function_trace.id] = dict()

        key = f"{client_executed_function_trace.module_name}:{client_executed_function_trace.name}"
        call_count = __FUNCTION_CALL_COUNT_MAP__[
            root_function_trace.id].get(key, 0) + 1
        __FUNCTION_CALL_COUNT_MAP__[root_function_trace.id][key] = call_count

        # If mock is found for the call count, return mocked output
        mock_for_function = get_mocks_for_function(
            function_config,
            client_executed_function_trace.module_name,
            client_executed_function_trace.name,
            call_count
        )

        if mock_for_function:
            logger.info(f"Found mocks for function {function_detail}")
            client_executed_function_trace.execution_context["is_mocked"] = True
            if mock_for_function.get("errorToThrow", None):
                raise Exception(mock_for_function["errorToThrow"])

            return mock_for_function.get("output", None)
    logger.debug(
        f"Could not find mocks for {function_detail}. Running original client function.")
    return decorated_client_function(*args, **kwargs)


def get_config_for_executed_client_function(client_executed_function_trace, frame):

    if not client_executed_function_trace.parent_id:
        while frame:
            if FUNCTION_ROOT_MAP.get(frame, None):

                execution_id = FUNCTION_ROOT_MAP.get(frame)
                function_config = FUNCTION_CONFIG_MAP.get(execution_id)
                return function_config

            frame = frame.f_back
    else:
        parent_instance = get_cache_value(
            Namespaces.client_function_trace_by_id, client_executed_function_trace.parent_id
        )

        if not parent_instance:
            raise Exception("Parent ID set incorrectly.")

        execution_id = parent_instance.execution_context.get(
            "execution_id", None)

        if not execution_id:
            raise Exception("Execution ID not set")

        function_config = FUNCTION_CONFIG_MAP.get(execution_id, [None, None])
        return function_config

    return None


def record_function_run_trace(execution_id):
    FUNCTION_TRACE_MAP[execution_id] = True


def get_mocks_for_function(function_config, module_name, function_name, call_count):
    if function_config.get("context", None) and isinstance(function_config["context"], dict):

        mocks: dict = function_config["context"].get("mocks", dict()) or dict()

        if len(mocks.keys()) < 1:
            return None

        mocks_for_function = mocks.get(f"{module_name}:{function_name}", None)

        if mocks_for_function and isinstance(mocks_for_function, dict):
            # Acount for integer or string keys
            mock_value = mocks_for_function.get(
                str(call_count), None) or mocks_for_function.get(call_count, None)

            if mock_value and isinstance(mock_value, dict):
                return mock_value

    return None
