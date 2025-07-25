# utils/logger.py
import logging
from colorama import Fore, Style

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplication or broken ones
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt=f'[{Fore.YELLOW}%(asctime)s] {Fore.LIGHTRED_EX}[%(levelname)s] {Fore.GREEN}%(name)s: {Fore.BLUE}%(message)s{Style.RESET_ALL}',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger
