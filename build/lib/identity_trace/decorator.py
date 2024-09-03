import inspect
import functools

from .constants import DEFAULT_FUNCTION_SPECIFIC_CONFIG
from .registry import get_cache_value, Namespaces


get_client_function_decorator = functools.partial(
    get_cache_value, Namespaces.client_function_callbacks, "decorator"
)


def watch(name = None, description = None, config = None):
    '''
        Decorator to wrap client code functions to monitor inputs and outputs of the function depending 
        on the configuration.

        @param name {string}: Optional name of the function. If this name is provided it will be registered 
        with this name in the registry.
        @param description {string}: Optional description of the function defining what the function is doing.
        @param config: Optional configuration for the function. If this config is provided, then for this
        function, agent will ignore the global config.
    '''

    current_frame = inspect.currentframe()
    caller_module_frame = current_frame.f_back

    package_name = caller_module_frame.f_globals['__package__']
    file_name = caller_module_frame.f_globals['__file__']
    module_name = caller_module_frame.f_globals['__name__']
    
    # Return the decorator while providing metadata
    return _internal_watch(
        name,
        description,
        config,
        module_name,
        file_name,
        package_name
    )



def _internal_watch(
        name,
        description,
        config,
        module_name,
        file_name,
        package_name
):
    
    function_specific_config = dict()
    function_specific_config.update(DEFAULT_FUNCTION_SPECIFIC_CONFIG)
    if config:
        function_specific_config.update(config)
    # Return the decorator while providing metadata
    return functools.partial(
        get_client_function_decorator(), # get the registered decorator from the registry
        module_name,
        package_name,
        file_name,
        name, # Function name
        description, # Function description
        function_specific_config, # Config set by user
    )