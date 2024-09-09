import sys
import os
import json

from .logger import logger

# Get the script's path
script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)


def read_json_file_in_identity_folder(file_name):
    file_name = f"__identity__/{file_name}"
    return read_json_file_from_project_root(file_name)
    

def read_json_file_from_project_root(file_name):


    # Read the run file
    if script_directory:
        file_name = f"{script_directory}/{file_name}"

    file = None
    try:
        logger.debug(f"Reading file {file_name}.")
        file = open(file_name, "r")
        file_content_string = file.read()
        file.close()
    except Exception as e:
        raise Exception((
            f"Could not read from run file. Run ID:{file_name}\n"
            f"Error: {str(e)}"
        ))

    # parse json
    file_content_json = None
    try:
        file_content_json = json.loads(file_content_string)
    except:
        raise Exception(
            f"Could not parse JSON config from run file. {str(file_content_string)}"
        )

    return file_content_json