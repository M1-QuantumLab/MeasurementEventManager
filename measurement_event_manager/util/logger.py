'''
Basic logger using the logging stdlib, configurable to both file and/or console
logging.

From https://gist.github.com/SamWolski/61eac3f62f68b8137c126fb32cd4ea3f
'''

from datetime import datetime
import logging
import os
import sys

def quick_config(logger,
                 console_log_level=logging.INFO, file_log_level=logging.DEBUG,
                 console_fmt='[%(asctime)s] %(message)s',
                 console_datefmt='%y-%m-%d %H:%M:%S',
                 log_file_name=None,
                 file_fmt='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
                 file_datefmt='%y-%m-%d %H:%M:%S',
                 file_log_dir='logs',
    ):
    """Rapidly configure a logger with a console and/or file handler.
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
