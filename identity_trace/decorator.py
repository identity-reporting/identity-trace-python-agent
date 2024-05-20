

from .registry import register_frame, is_frame_registered, remove_frame, register_function, get_function_processor_callbacks
from .tracer import trace_function
import inspect
import json
import datetime


class FunctionTrace:
    config = {
        'trace_input': True,
        'trace_output': True,
        'serializer': lambda o: json.dumps(o)
    }
    package_name = None
    file_name = None
    module_name = None
    name = None
    description = None
    function_id = None

    input = None
    output = None

    parent_id = None
    executed_successfully = None
    error = None

    start_time = None
    end_time = None
    execution_id = None

    children = []

    execution_context = None

    def serialize(self):
        return dict(
            config={
                'trace_input': self.config['trace_input'],
                'trace_output': self.config['trace_output'],
            },
            executionContext = self.execution_context,
            packageName=self.package_name,
            fileName=self.file_name,
            moduleName=self.module_name,
            name=self.name,
            description=self.description,
            functionID=self.function_id,
            _id = self.function_id,
            input=json.loads(self.input),
            output=json.loads(self.output) if self.output else self.output,
            parentID=self.parent_id,
            executedSuccessfully=self.executed_successfully,
            error=self.error,
            startTime=self.start_time,
            endTime=self.end_time,
            executionID = self.execution_id
        )


def watch(name=None, description='', config=None):

    def wrapper(func):

        if not callable(func):
            raise Exception('Can only watch function.')

        current_frame = inspect.currentframe()
        caller_module_frame = current_frame.f_back

        package_name = caller_module_frame.f_globals['__package__']
        file_name = caller_module_frame.f_globals['__file__']
        module_name = caller_module_frame.f_globals['__name__']
        function_name = name or func.__name__
        function_id = id(func)


        
        

        def inner(*args, **kwargs):

            # register current function run
            frame = inspect.currentframe()
            import uuid


            parent_execution_context, parent_frame = find_parent(frame)
            function_id = str(uuid.uuid4())
            execution_context = get_new_execution_context(function_id)

            parent_id = None

            if parent_execution_context:
                if parent_execution_context.get("_action", None) == "copy_context":
                    remove_frame(parent_frame)
                if parent_execution_context.get("function_id", None):
                    parent_id = parent_execution_context["function_id"]
                
                parent_context_copy = copy_parent_context(parent_execution_context)
                execution_context.update(parent_context_copy)

            register_frame(frame, execution_context)

            function_trace_instance = FunctionTrace()
            function_trace_instance.execution_context = dict()
            function_trace_instance.name = function_name
            function_trace_instance.file_name = file_name
            function_trace_instance.package_name = package_name
            function_trace_instance.function_id = function_id
            function_trace_instance.parent_id = parent_id
            function_trace_instance.module_name = module_name
            
            function_trace_instance.execution_id = str(uuid.uuid4())

            function_trace_instance.description = description
            function_trace_instance.config.update(config or dict())

            # serialize input
            if function_trace_instance.config.get('trace_input', None):
                function_trace_instance.input = function_trace_instance.config['serializer']([
                    *args, kwargs
                ])

            try:
                function_trace_instance.start_time = datetime.datetime.now().timestamp()
                output = None
                
                funtion_to_call = func
                callbacks = get_function_processor_callbacks()
                if callbacks:
                    funtion_to_call = callbacks(function_trace_instance, funtion_to_call)
                
                output = funtion_to_call(*args, **kwargs)
                
                function_trace_instance.end_time = datetime.datetime.now().timestamp()

                if function_trace_instance.config.get('trace_output', None):
                    # serialize input
                    function_trace_instance.output = function_trace_instance.config['serializer'](
                        output)

                function_trace_instance.executed_successfully = True
                return output
            except Exception as e:
                function_trace_instance.end_time = datetime.datetime.now().timestamp()
                function_trace_instance.executed_successfully = False
                function_trace_instance.error = str(e)
                raise e
            finally:
                remove_frame(frame)
                # this means execution is complete
                trace_function(function_trace_instance)

        register_function(function_name=function_name, func=inner)
        return inner

        

    return wrapper


def find_parent(frame):
    frame = frame.f_back
    while frame:
        parent_execution_context = is_frame_registered(frame)
        if parent_execution_context:
            return [parent_execution_context, frame]
        frame = frame.f_back

    return [None, None]


def copy_parent_context(parent_execution_context: dict):

    new_context = dict()
    new_context.update(parent_execution_context)
    if new_context.get("internal_meta", None):
        del new_context["internal_meta"]

    if new_context.get("function_id", None):
        del new_context["function_id"]

    return new_context

def get_new_execution_context(function_id):

    return dict(
        function_id = function_id,
    )