"""Logger module for the CV renderer package."""

import logging


def make_logger(module_name: str) -> logging.Logger:
    """Make a logger for the current module."""
    logger_name = module_name.split(".", 1)[-1]
    return logging.getLogger(logger_name)
