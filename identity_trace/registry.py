
from .logger import logger
class Namespaces:

    client_function_wrapper_call_frame = "client_function_wrapper_call_frame"
    client_function_trace_by_id = "client_function_trace_by_id"

    run_file_action = "run_file_action"
    tracer_callbacks = "tracer_callbacks"

    client_function_callbacks = "client_function_callbacks"


__cache__ = dict()

def set_cache_value(namespace, key, value):

    logger.debug(f"Setting Cache Value", namespace, key, value)

    if not namespace:
        raise Exception("Namespace should be provided when setting a cache value.")

    if not isinstance(key, str):
        raise Exception(f"Cache key should be a string but found {type(key).__name__}.")
    
    if not __cache__.get(namespace, None):
        __cache__[namespace] = dict()
    
    __cache__[namespace][key] = value

def get_cache_value(namespace, key):


    target_dict = __cache__.get(namespace, None)

    if target_dict and isinstance(target_dict, dict):
        
        res = target_dict.get(key, None)
    else:
        res = None
    
    logger.debug("Getting Cache Value.", namespace, key, res)

    return res

def delete_cache_value(namespace, key):

    target_dict = __cache__.get(namespace, None)

    if target_dict and isinstance(target_dict, dict):

        logger.debug("Deleting Cache Value", namespace, key)    
        
        if target_dict.get(key, None):
            del target_dict[key]




__client_function_runner__ = dict(runner = None)

def set_client_function_runner(callback):
    __client_function_runner__["runner"] = callback

def get_client_function_runner():
    return __client_function_runner__["runner"]
