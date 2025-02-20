import logging
import coloredlogs
import os
from datetime import datetime


# Set logger levels for specific libraries
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

logger = logging.getLogger()

# Custom filter to ignore unwanted lines
class IgnoreUnwantedFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        # Ignore "Using selector:" and "socket.send() raised exception" messages
        if "Using selector:" in msg or "socket.send() raised exception" in msg:
            return False
        return True

logger.addFilter(IgnoreUnwantedFilter())

# Configure coloredlogs to print to console
coloredlogs.install(level='DEBUG',
                    fmt='%(asctime)s - %(message)s - [%(filename)s:%(lineno)d]',
                    level_styles={
                        'debug': {'color': 'blue'},
                        'info': {'color': 'green'},
                        'warning': {'color': 'yellow'},
                        'error': {'color': 'red'},
                        'critical': {'color': 'red', 'bold': True}
                    })
