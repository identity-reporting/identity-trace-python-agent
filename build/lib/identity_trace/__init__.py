from .runner import execute_run_file
from .decorator import watch




def _init():
    from .orchestration import orchestrate
    orchestrate()


_init()