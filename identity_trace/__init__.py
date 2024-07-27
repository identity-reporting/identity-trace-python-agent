from .runner import initialize




def _init():
    from .orchestration import orchestrate
    orchestrate()


_init()