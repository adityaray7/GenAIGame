import logging
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Define a custom formatter that adds colors based on the log level
class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        message = super().format(record)
        return f"{log_color}{message}"

# Create a custom logger
logger = logging.getLogger('gameLogger')
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()             # Console logger
f_handler = logging.FileHandler('game.log')   # File logger

# Create formatters and add them to handlers
c_format = ColorFormatter('%(asctime)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# # Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

if __name__ == '__main__':

    # Log messages for testing
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')
