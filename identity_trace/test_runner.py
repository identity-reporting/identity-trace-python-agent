import functools
from .registry import register_tracer_callback, set_client_function_runner

__function_call_count_map__ = {}
    

def _has_mock_for_function(module_name, function_name, function_mocks, call_count):

    key = f"{module_name}:{function_name}"
    if function_mocks.get(key):

        if function_mocks[key].get(str(call_count), None):

            return function_mocks[key][str(call_count)]
    
    return False

def test_run_action(function_config, on_function_complete_trace):

    set_client_function_runner(
        functools.partial(client_function_runner, function_config)
    )
    register_tracer_callback("client_executed_function_finish", on_function_complete_trace)
    


def get_mocks_from_function_run_config(function_config):

    if function_config.get("context", None):

        if function_config["context"].get("test_run"):

            test_run_context = function_config["context"]["test_run"]

            mocks: dict = test_run_context.get("mocks", dict())

            if len(mocks.keys()) < 1:
                return None
            
            return mocks

    return None

def client_function_runner(
        function_run_config, 
        client_executed_function_trace,
        client_function, 
        *args, **kwargs
):
    '''
        Runs the client function and handles function mocks defined in run function config.
    '''

    key = f"{client_executed_function_trace.module_name}:{client_executed_function_trace.name}"

    if client_executed_function_trace.name == "add_item_to_ticket":
        print("ssss")

    call_count = __function_call_count_map__.get(key, 0) + 1
    __function_call_count_map__[key] = call_count
    
    function_mocks = get_mocks_from_function_run_config(function_run_config)
    mock_for_function = None

    if function_mocks:
        mock_for_function = _has_mock_for_function(
            client_executed_function_trace.module_name,
            client_executed_function_trace.name,
            function_mocks,
            call_count
        )

    client_executed_function_trace.execution_context["test_run"] = {}
    if mock_for_function:
        client_executed_function_trace.execution_context["test_run"]["is_mocked"] = True
        if mock_for_function.get("errorToThrow", None):
            raise Exception(mock_for_function["errorToThrow"])
        else:
            return mock_for_function["output"]
            
    else:
        return client_function(*args, **kwargs)



        