import jsonpickle


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
    
    res = requests.post('http://localhost:8002/save-function-execution-trace',
                        json=trace)

    print(res, "this is another")


def get_environment_details():
    import uuid
    return dict(
        traceID=str(uuid.uuid4()),
        # get this from env
        environmentName="some_env",
    )
