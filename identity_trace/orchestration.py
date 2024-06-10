from .registry import register_run_action, register_tracer_callback, set_client_function_decorator
from .test_run import test_run_action
from .tracer import general_preprocessing_tracer, general_postprocessing_tracer,\
    general_function_trace_callback

from .wrappers import general_wrapper

__local_map__ = {}

def register_run_actions():
    if __local_map__.get("run_actions", False):
        return
    
    register_run_action("test_run", test_run_action)

    __local_map__["run_actions"] = True


def register_tracer_callbacks():

    if __local_map__.get("tracer", False):
        return
    
    register_tracer_callback("client_executed_function_preprocess", general_preprocessing_tracer)
    register_tracer_callback("client_executed_function_postprocess", general_postprocessing_tracer)
    register_tracer_callback("client_executed_function_finish", general_function_trace_callback)

    __local_map__["tracer"] = True


def register_client_function_wrapper():

    if __local_map__.get("wrapper", False):
        return
    
    set_client_function_decorator(general_wrapper)

    __local_map__["wrapper"] = True



def orchestrate():

    register_run_actions()
    register_client_function_wrapper()
    register_tracer_callbacks()