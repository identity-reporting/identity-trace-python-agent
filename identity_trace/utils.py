import sys
import os
import json

from .logger import logger

# Get the script's path
script_path = sys.argv[0]

# Get the directory path where the script was executed from
script_directory = os.path.dirname(script_path)


def read_json_file_in_identity_folder(file_name):
    run_file_id = f"__identity__/{file_name}"
    # Read the run file
    if script_directory:
        run_file_id = f"{script_directory}/{run_file_id}"

    file = None
    try:
        logger.debug(f"Reading file {run_file_id}.")
        file = open(run_file_id, "r")
        run_file_config_string = file.read()
        file.close()
    except Exception as e:
        raise Exception((
            f"Could not read from run file. Run ID:{run_file_id}\n"
            f"Error: {str(e)}"
        ))

    # parse json
    run_file_config = None
    try:
        run_file_config = json.loads(run_file_config_string)
    except:
        raise Exception(
            f"Could not parse JSON config from run file. {str(run_file_config)}"
        )

    return run_file_config



