

_function_registry = {}
__function_registry = {}


def register_frame(frame, client_executed_function_trace_instance):
    _function_registry[_get_frame_id(frame)] = client_executed_function_trace_instance


def is_frame_registered(frame):
    return _function_registry.get(_get_frame_id(frame), False)


def remove_frame(frame):
    if _function_registry.get(frame, None):
        del _function_registry[frame]


def _get_frame_id(frame):
    return id(frame)


def register_function(function_name, func):
    __function_registry[function_name] = func


def get_function_by_name(function_name):
    return __function_registry.get(function_name, None)

def remove_function(function_name):

    if __function_registry.get(function_name, None):
        del __function_registry[function_name]


__run_actions__ = {}

def register_run_action(action_name, callback):
    __run_actions__ [action_name] = callback

def get_run_action(action_name):

    return __run_actions__.get(action_name, None)

def remove_run_action(action_name):
    del __run_actions__ [action_name]


__client_function_decorator__ = {}

def set_client_function_decorator(callback):

    __client_function_decorator__["callback"] = callback

def get_client_function_decorator():

    return __client_function_decorator__["callback"]



__tracer_callbacks__ = {}

def register_tracer_callback(action_name, callback_function):
    __tracer_callbacks__[action_name] = callback_function

def remove_tracer_callback(action_name):
    if __tracer_callbacks__.get(action_name):
        del __tracer_callbacks__[action_name] 

def get_tracer_callback(action_name):
    return __tracer_callbacks__.get(action_name, None)



__client_function_runner__ = dict(runner = None)

def set_client_function_runner(callback):
    __client_function_runner__["runner"] = callback

def get_client_function_runner():
    return __client_function_runner__["runner"]
