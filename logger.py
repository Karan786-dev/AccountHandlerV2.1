import logging
import coloredlogs
import os
import sys
from datetime import datetime

logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("telethon").setLevel(logging.ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('faker').setLevel(logging.ERROR)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class IgnoreUnwantedFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if "Using selector:" in msg or "socket.send() raised exception" in msg:
            return False
        return True

logger.addFilter(IgnoreUnwantedFilter())
logging.getLogger('asyncio').addFilter(IgnoreUnwantedFilter())
logging.getLogger('selector_events').addFilter(IgnoreUnwantedFilter())

for handler in logger.handlers[:]:
    logger.removeHandler(handler)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(message)s - [%(filename)s:%(lineno)d]')
stdout_handler.setFormatter(formatter)
stderr_handler.setFormatter(formatter)

error_file_handler = logging.FileHandler('error.log')
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(formatter)

logger.addHandler(error_file_handler)
logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)

coloredlogs.install(level='DEBUG',
                    fmt='%(asctime)s - %(message)s - [%(filename)s:%(lineno)d]',
                    level_styles={
                        'debug': {'color': 'blue'},
                        'info': {'color': 'green'},
                        'warning': {'color': 'yellow'},
                        'error': {'color': 'red'},
                        'critical': {'color': 'red', 'bold': True}
                    },
                    logger=logger)