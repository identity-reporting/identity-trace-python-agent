import jsonpickle

LOG_LEVELS = dict(
    debug = 1,
    info = 2,
    log = 3,
    error = 4
)
class Logger:

    def __init__(self, log_level = 3) -> None:
        try:
            self.log_level = int(log_level)
        except Exception as e:
            raise Exception((
                f"Could not initialize the logger because of invalid value for log_level argument. "
                f"Provided log_level {log_level}. \n"
                f"{str(e)}"
            ))

    def log(self, message):
        if self.log_level > LOG_LEVELS['log']:
            return
        print(message)
    
    def error(self, message):
        if self.log_level > LOG_LEVELS['error']:
            return
        print(str(message))
    
    def info(self, message):
        if self.log_level > LOG_LEVELS['info']:
            return
        print(str(message))
    
    def debug(self, message, *args):
        if self.log_level > LOG_LEVELS['debug']:
            return
        
        print(str(message), *args)
    

logger = Logger(log_level=2)