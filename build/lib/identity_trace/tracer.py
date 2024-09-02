import jsonpickle
import os
import sys
import functools
from .registry import (
    set_cache_value,
    delete_cache_value,
    get_cache_value, Namespaces
)
from .logger import logger


register_frame = functools.partial(set_cache_value, Namespaces.client_function_wrapper_call_frame)
remove_frame = functools.partial(delete_cache_value, Namespaces.client_function_wrapper_call_frame)
is_frame_registered = functools.partial(get_cache_value, Namespaces.client_function_wrapper_call_frame)


register_function = functools.partial(set_cache_value, Namespaces.client_function_trace_by_id)
get_function_by_name = functools.partial(get_cache_value, Namespaces.client_function_trace_by_id)
remove_function = functools.partial(delete_cache_value, Namespaces.client_function_trace_by_id)

# Get the script's path
script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)


def general_preprocessing_tracer(
    function_specific_config, client_executed_function_trace, function_call_frame, function_input
):
    '''
        Tracer callback which is executed before the client function execution. This function will
        respond to `client_executed_function_preprocess` signal emitted in the client function
        wrapper.

        @param function_specific_config: User defined config for client function
        @param client_executed_function_trace: ClientExecutedFunctionTrace instance. Since this
        callback is executed before the client function is called, client_executed_function_trace won't
        have any output or error details attached.
        @param function_call_frame: Python function frame of client function wrapper.
        @param function_input: Client function's input in the for of array. Last element in 
        the array will be all the name args (**kwargs). [*args, kwargs: dict]
    '''
    logger.debug(f"Started pre processing for {client_executed_function_trace.name}")
    copy_input = function_specific_config["copy_input"]
    input_serializer = function_specific_config["input_serializer"]

    # Copy input
    input_copy = None
    
    if copy_input:
        try:
            input_copy = input_serializer(function_input)
            logger.debug(f"Created a copy of input.", input_copy)
        except Exception as e:
            client_executed_function_trace.execution_context["copy_input_error"] = str(e)
    
    client_executed_function_trace.input = input_copy
    client_executed_function_trace.execution_context["copy_input"] = copy_input

    # Find parent
    find_parent = function_specific_config["find_parent"]
    if find_parent:

        logger.debug("Finding parent for", client_executed_function_trace.name)
        # register the frame
        register_frame(_get_frame_id(function_call_frame), client_executed_function_trace)

        # If we should find parent, then this function should be registered, so that its children
        # can find it as well
        register_function(client_executed_function_trace.id, client_executed_function_trace)

        parent_frame = function_call_frame.f_back
        while parent_frame:

            parent_trace_instance = is_frame_registered(_get_frame_id(parent_frame))
            if parent_trace_instance:
                client_executed_function_trace.parent_id = parent_trace_instance.id
                logger.debug((
                    f"Found parent ({parent_trace_instance.name}) for "
                    f"{client_executed_function_trace.name}."
                ))
                break

            parent_frame = parent_frame.f_back





def general_postprocessing_tracer(
    function_specific_config, client_executed_function_trace, function_call_frame, function_output
):
    '''
        Tracer callback which is executed after the client function execution. This function will
        respond to `client_executed_function_postprocess` signal emitted in the client function
        wrapper.

        @param function_specific_config: User defined config for client function
        @param client_executed_function_trace: ClientExecutedFunctionTrace instance.
        @param function_call_frame: Python function frame of client function wrapper.
        @param function_output: Client function's output.
    '''
    copy_output = function_specific_config["copy_output"]

    output_serializer = function_specific_config["output_serializer"]

    logger.debug("Post processing started for ", client_executed_function_trace.name)

    # Copy output
    output_copy = None
    if copy_output:
        try:
            output_copy = output_serializer(function_output)
            logger.debug("Created output copy", output_copy)
        except Exception as e:
            client_executed_function_trace.execution_context["copy_output_error"] = str(e)
    
    client_executed_function_trace.output = output_copy
    client_executed_function_trace.execution_context["copy_output"] = copy_output
    
    

    find_parent = function_specific_config["find_parent"]
    if find_parent:
        # remove the registered frame
        remove_frame(_get_frame_id(function_call_frame))
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
    '''
        Tracer callback which is executed after the client function execution. This function will
        respond to `client_executed_function_finish` signal emitted in the client function
        wrapper.

        @param function_specific_config: User defined config for client function
        @param client_executed_function_trace: ClientExecutedFunctionTrace instance.
        @param function_call_frame: Python function frame of client function wrapper.
    '''

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


def _get_frame_id(frame):
    return str(id(frame))