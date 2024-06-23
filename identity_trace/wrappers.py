

import json
import inspect
import time
import uuid

from .registry import get_tracer_callback, get_client_function_runner

class ClientExecutedFunctionTrace:
    config = None
    package_name = None
    file_name = None
    module_name = None

    name = None
    description = None

    id = None

    input = None
    output = None

    parent_id = None
    executed_successfully = None
    error = None

    start_time = None
    end_time = None
    execution_id = None

    children = None

    execution_context = None


    def __init__(self) -> None:
        self.execution_context = dict()
        self.children = []
        self.id = str(uuid.uuid4())

    def serialize(self):
        return dict(
            config=self.config,
            executionContext = self.execution_context,
            packageName=self.package_name,
            fileName=self.file_name,
            moduleName=self.module_name,
            name=self.name,
            description=self.description,
            id = self.id,
            input=json.loads(self.input),
            output=json.loads(self.output) if self.output else self.output,
            parent_ID=self.parent_id,
            executedSuccessfully=self.executed_successfully,
            error=self.error,
            startTime=self.start_time,
            endTime=self.end_time,
            children = [f.serialize() for f in self.children]
        )


def general_wrapper(
        module_name,
        package_name,
        file_name,
        function_name,
        function_description,
        function_specific_config,
        decorated_client_function
    ):
    '''
        @param module_name: Module name in which the client function is defined.
        @param package_name: Package name in which the client function is defined.
        @param file_name: File name in which the client function is defined.
        @param function_name: Name for this function set by the user
        @param function_description: Description for this function set by the user
        @param function_specific_config: Configuration for this function
        @param post_processing_callback: Callback for pos processing the ClientExecutedFunctionTrace. 
        Additional details can be set on the instance like test runner will set mocking metadata in the
        execution context.
        @param decorated_client_function: Client function that is being decorated

        General decorator for client functions. Responsible for setting metadata on
        ClientExecutedFunctionTrace according to the config. This decorator will create 
        a new instance of ClientExecutedFunctionTrace for every function call.
    '''

    name = function_name or decorated_client_function.__name__
    description = function_description or None

    def function_handler(*args, **kwargs):
        '''
            Wrapper function that gets executed before client function gets called.
            This wrapper is responsible for gathering data about the client function and 
            emitting a trace to the collector.
        '''
        current_frame = inspect.currentframe()

        client_executed_function_trace = ClientExecutedFunctionTrace()
        client_executed_function_trace.package_name = package_name
        client_executed_function_trace.module_name = module_name
        client_executed_function_trace.file_name = file_name
        client_executed_function_trace.name = name
        client_executed_function_trace.description = description
        client_executed_function_trace.config = function_specific_config

        _call_callback(
            get_tracer_callback("client_executed_function_preprocess"),
            function_specific_config,
            client_executed_function_trace,
            current_frame,
            [*args, kwargs]
        )

        # Raise error at the end of the function
        client_thrown_error = None
        
        output = None

        # Run function here
        try:
            # If there is a client function runner registered
            # Let the runner handle the client function call
            client_function_runner = get_client_function_runner()
            if client_function_runner:
                client_executed_function_trace.start_time = int(time.time() * 1000)
                output = client_function_runner(client_executed_function_trace, decorated_client_function,  *args, **kwargs)
            else:
                client_executed_function_trace.start_time = int(time.time() * 1000)
                output = decorated_client_function(*args, **kwargs)
            
            client_executed_function_trace.end_time = int(time.time() * 1000)
            client_executed_function_trace.executed_successfully = True
        except Exception as e:
            client_executed_function_trace.end_time = int(time.time() * 1000)
            client_thrown_error = e
            client_executed_function_trace.error = str(e)
            client_executed_function_trace.executed_successfully = False
        
        # Post processing
        _call_callback(
            get_tracer_callback("client_executed_function_postprocess"),
            function_specific_config,
            client_executed_function_trace,
            current_frame,
            output
        )

        # After finish trace
        _call_callback(
            get_tracer_callback("client_executed_function_finish"),
            function_specific_config,
            client_executed_function_trace,
            current_frame
        )

        # Throw error if client function threw error
        if client_thrown_error:
            raise client_thrown_error
        
        return output
    
    return function_handler
        


def _call_callback(callback, *args):

    if callback and callable(callback):
        callback(*args)