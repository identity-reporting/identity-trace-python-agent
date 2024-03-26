import importlib
import json
from registry import get_function_by_name, register_frame
from tracer import register_trace_callback
import os
import inspect
import uuid
import requests
import functools


file_path = os.path.dirname(os.path.realpath(__file__)) + '/config.json'


def run_test():

    print(file_path)

    with open(file_path, 'r') as file:
        # Load the JSON data from the file
        data = json.load(file)
        module_name = data["functionMeta"]["moduleName"]
        function_name = data["functionMeta"]["name"]
        input_to_pass = data["inputToPass"]
        test_case_id = data["_id"]
        importlib.import_module(module_name)
        func = get_function_by_name(function_name)
        if not func:
            raise Exception("Function did not register on import.")

        frame = inspect.currentframe()

        context = dict(
            function_id=id(run_test),
            is_internal_execution=True,
            execution_id=id(run_test),
            description="Function Test Run",
            internal_meta=dict(
                invoked_for_test=True
            )
        )

        register_frame(frame, context)
        callback_id = str(uuid.uuid4())
        register_trace_callback(callback_id, functools.partial(send_trace_to_server, test_case_id))

        try:
            func(**input_to_pass)
        except Exception as e:
            ...



def send_trace_to_server(test_case_id, trace):

    trace["testCaseId"] = test_case_id

    res = requests.post('http://localhost:8002/save-test-run',
                        json=trace)
    
    print(res)
    return True