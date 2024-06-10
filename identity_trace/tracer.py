import jsonpickle
import os
import sys
from .registry import register_frame, remove_frame, is_frame_registered, \
    get_function_by_name, register_function, remove_function



# Get the script's path
script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)


_traces = []
__trace_callbacks = dict()
def register_trace_callback(id = None, func = None):
    __trace_callbacks[id] = func

def remove_trace_callback(id = None):
    if __trace_callbacks.get(id, None):
        del __trace_callbacks[id]


def trace_function(function_trace_instance):

    _traces.append(function_trace_instance)
    # this means execution is complete
    if not function_trace_instance.parent_id:
        send_execution_trace(_traces)
        _traces.clear()
       


def send_execution_trace(traces):
    print(
        jsonpickle.encode(traces)
    )

    

    import requests
    import json

    function_traces_dicts = [t.serialize() for t in traces]
    trace = dict(
        type='function_trace',
        **get_environment_details(),
        data=function_traces_dicts
    )


    for id, callback_fn in __trace_callbacks.items():
        res = callback_fn(trace)
        if res:
            return
    
    res = requests.post('http://localhost:8002/executed_function/save-function-execution-trace',
                        json=trace)

    print(res, "this is another")


def get_environment_details():
    import uuid
    return dict(
        traceID=str(uuid.uuid4()),
        # get this from env
        environmentName="some_env",
    )

def general_preprocessing_tracer(
    function_specific_config, client_executed_function_trace, function_call_frame, function_input
):
    
    # register the frame
    register_frame(function_call_frame, client_executed_function_trace)

    copy_input = function_specific_config["copy_input"]
    
    input_serializer = function_specific_config["input_serializer"]

    # Copy input
    input_copy = None
    
    if copy_input:
        try:
            input_copy = input_serializer(function_input)
        except Exception as e:
            client_executed_function_trace.execution_context["copy_input_error"] = str(e)
    
    client_executed_function_trace.input = input_copy
    client_executed_function_trace.execution_context["copy_input"] = copy_input

    # Find parent
    find_parent = function_specific_config["find_parent"]
    if find_parent:

        # If we should find parent, then this function should be registered, so that its children
        # can find it as well
        register_function(client_executed_function_trace.id, client_executed_function_trace)

        parent_frame = function_call_frame.f_back
        while parent_frame:

            parent_trace_instance = is_frame_registered(parent_frame)
            if parent_trace_instance:
                client_executed_function_trace.parent_id = parent_trace_instance.id
                break

            parent_frame = parent_frame.f_back





def general_postprocessing_tracer(
    function_specific_config, client_executed_function_trace, function_call_frame, function_output
):
    copy_output = function_specific_config["copy_output"]

    output_serializer = function_specific_config["output_serializer"]


    # Copy output
    output_copy = None
    if copy_output:
        try:
            output_copy = output_serializer(function_output)
        except Exception as e:
            client_executed_function_trace.execution_context["copy_output_error"] = str(e)
    
    client_executed_function_trace.output = output_copy
    client_executed_function_trace.execution_context["copy_output"] = copy_output
    
    remove_frame(function_call_frame)

    find_parent = function_specific_config["find_parent"]
    if find_parent:
        # Remove function if it was registered
        remove_function(client_executed_function_trace.id)
    
    # If the function has parent, append this function to parent's children
    if client_executed_function_trace.parent_id:
        parent_tace_instance = get_function_by_name(client_executed_function_trace.parent_id)

        if not parent_tace_instance:
            raise Exception((
                f"Parent ID ({client_executed_function_trace.parent_id}) is set on "
                f"client executed function ({client_executed_function_trace.name}) but "
                f"parent function ID ({client_executed_function_trace.parent_id}) is not registered."
            ))
        
        parent_tace_instance.children.append(
            client_executed_function_trace
        )


def general_function_trace_callback(function_specific_config, client_executed_function_trace, function_call_frame):
    if client_executed_function_trace.parent_id:
        return
    
    
    
    # If this is a root function, write the trace to file
    file_path = f"__identity__/ExecutedFunction/{client_executed_function_trace.id}.json"

    if script_directory:
        file_path = f"{script_directory}/{file_path}"

    file = open(file_path, "w")
    file.write(
        jsonpickle.encode(client_executed_function_trace.serialize(), False)
    )
    file.close()


