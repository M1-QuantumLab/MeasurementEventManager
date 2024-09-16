'''
Basic logging config and utilities
'''

from datetime import datetime
import logging
import os
import sys
from typing import Optional


###############################################################################
## Logging config
###############################################################################


## Log level string/value parsing
#################################


_STR2LOG = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def parse_log_level(level_str_or_int: str | int) -> int:
    """Parse a logging level, either as an int or as a string corresponding
    to a log level from the logging stdlib

    Args:
        level_str_or_int: Logging level specification.

    Returns:
        The logging level as an int.

    Raises:
        ValueError: The level specification is not recognized and cannot be
            cast to an int.
    """

    ## Check if this is one of the predefined levels
    if level_str_or_int in _STR2LOG:
        return _STR2LOG[level_str_or_int]

    ## Otherwise, try and parse it as an int
    try:
        level = int(level_str_or_int)
    except ValueError as e:
        raise ValueError("Cannot parse {} as a logging level".format(level_str_or_int))
    return level


## Logging config
#################


def quick_config(
    logger: logging.Logger,
    console_log_level: Optional[int] = logging.INFO,
    file_log_level: Optional[int] = logging.DEBUG,
    console_fmt: str = '[%(asctime)s] %(message)s',
    console_datefmt: str ='%y-%m-%d %H:%M:%S',
    log_file_name: Optional[str] = None,
    file_fmt: str = '%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    file_datefmt: str = '%y-%m-%d %H:%M:%S',
    file_log_dir: str = 'logs',
    ) -> logging.Logger:
    """Rapidly configure a logger with a console and/or file handler.

    Configurable to both file and/or console logging.

    From https://gist.github.com/SamWolski/61eac3f62f68b8137c126fb32cd4ea3f

    Args:
        logger: Logger object to be configured.
        console_log_level: Logging level for console output; pass None to
            disable console output.
        file_log_level: Logging level for file output; pass None to disable
            file output.
        console_fmt: Message formatting for console output.
        console_datefmt: Timestamp formatting in console_fmt.
        log_file_name: File name prefix for file output; defaults to the name
            of the logger object.
        file_fmt: Message formatting for file output.
        file_datefmt: Timestamp formatting in file_fmt.
        file_log_dir: Base directory for storing logs.

    Returns:
        The logger object with configurations applied.
    """

    ## Add console handler
    if console_log_level is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_log_level)
        console_formatter = logging.Formatter(console_fmt, 
                                    datefmt=console_datefmt)
        console_handler.setFormatter(console_formatter)
        ## Add handler to logger
        logger.addHandler(console_handler)

    ## Add file handler
    if file_log_level is not None:
        ## Ensure target directory exists
        if not os.path.exists(file_log_dir):
            os.makedirs(file_log_dir)
        ## Set up log file
        log_file_name = logger.name if log_file_name is None else log_file_name
        log_file = '{}_{:%y%m%d_%H%M%S}.log'.format(log_file_name, datetime.now())
        log_path = os.path.join(file_log_dir, log_file)
        ## Initialize file handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(file_log_level)
        file_formatter = logging.Formatter(file_fmt,
                                    datefmt=file_datefmt)
        file_handler.setFormatter(file_formatter)
        ## Add handler to logger
        logger.addHandler(file_handler)

    ## Add NullHandler if no other handlers are configured
    ## NB we need to just check the emtpiness of the handlers list in py2.7
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    ## Set the level of the logger as the smallest of the handlers
    logger.setLevel(min(xx.level for xx in logger.handlers))

    return logger


## Redirecting streams to logger objects
########################################


class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance

    From https://stackoverflow.com/a/66209331, which handles newlines correctly

    To redirect to an existing logger, do something like:
    sys.stderr = StreamToLogger(logger, logging.ERROR)
    """

    def __init__(self, logger: logging.Logger, level: int):
        """
        Args:
            logger: Target logger object.
            level: Logging level.
        """
        self.logger = logger
        self.level = level
        self.buffer = []

    def write(self, msg):
        if msg.endswith("\n"):
            self.buffer.append(msg.removesuffix("\n"))
            self.logger.log(self.level, "".join(self.buffer))
            self.buffer = []
        else:
            self.buffer.append(msg)

    def flush(self):
        pass
