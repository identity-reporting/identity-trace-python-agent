
import sys
import os
import json
import importlib
import inspect
from .decorator import _internal_watch

from .logger import logger

script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)

# Throw Error
def initialize_with_config_file(file_name = None):
    
    user_config = read_config_file(file_name)

    process_user_config(user_config)



# Throw Error
def read_config_file(config_file_name = None):
    identity_config_file_name = config_file_name or "identity_config.json"

    

    file_path = identity_config_file_name
    # Read the run file
    if script_directory:
        file_path = f"{script_directory}/{file_path}"

    logger.debug(f"Reading user config file {identity_config_file_name}.")

    file = None
    try:
        file = open(file_path, "r")
        config_file_string = file.read()
        file.close()
    except Exception as e:
        raise Exception((
            f"Could not read from config file. Create 'identity_config.json' file in the root directory of your project.\n"
            f"Error: {str(e)}"
        ))

    # parse json
    user_config = None
    try:
        user_config = json.loads(config_file_string)
    except Exception as e:
        raise Exception(f"Could not parse JSON from config file. Error: {str(e)}. {str(config_file_string)}")

    validate_user_config(user_config)

    return user_config


def validate_user_config(config):
    return True

'''
    {
        "modules": {
            "example1": True // Will capture every callable in the file and wrap it
            "example2": ["some_func"] // Only wrap some_func in module example2
        }
    }
'''

def process_user_config(user_config):
    

    for module_name, value in user_config["modules"].items():

        try:
            logger.debug(f"Importing module {module_name} to decorate functions.")
            module = importlib.import_module(module_name)
            file_name = getattr(module, "__file__")
            package_name = getattr(module, "__package__")
        except Exception as e:
            raise Exception((
                f"Invalid module ({module_name}) specified in the config file. "
                f"Could not import module {module_name}."
                f"Error: {str(e)}"
            ))
        
        if value == True and not isinstance(value, list):
            # import module name
            # find every callable
            # wrap it
            logger.debug(f"decorating all functions in {module_name}.")
            for name, obj in inspect.getmembers(module):
                if (inspect.isfunction(obj) or inspect.isclass(obj)) and obj.__module__ == module_name:
                    decorated_function = wrap_function(
                        obj, name=obj.__name__, description=None, config=None,
                        file_name=file_name, module_name=module_name, package_name=package_name
                    )
                    setattr(module, name, decorated_function)


        else:
            # import module name
            # iterate over every callable present in the value
            # wrap it
            for name in value:
                function_name = None
                function_description = None
                function_config = None

                if isinstance(name, str):
                    function_name = name
                elif isinstance(name, dict):
                    function_name = name["name"]
                    function_description = name["description"]
                    function_config = name["config"]


                func = getattr(module, function_name, None)
                if not func or not callable(func):
                    raise Exception((
                        f"Invalid callable ({name}) specified inside module ({module_name}) in config file. "
                        f"{name} should be class or function."
                    ))

                decorated_function = wrap_function(
                    func, name=function_name, description=function_description, config=function_config,
                    file_name=file_name, module_name=module_name, package_name=package_name
                )
                setattr(module, function_name, decorated_function)
                



def wrap_function(client_function, name, description, config, module_name, file_name, package_name):
    logger.debug(f"Wrapping {name} in module {module_name}")
    decorator = _internal_watch(
        name=name,
        description=description,
        config=config,
        module_name=module_name,
        file_name=file_name,
        package_name=package_name
    )
    decorated_function = decorator(client_function)
    return decorated_function