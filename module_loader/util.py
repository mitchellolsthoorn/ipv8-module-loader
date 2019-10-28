"""
"""

from __future__ import absolute_import

# Default library imports
import logging
import os

# Constants
PACKAGE_INIT_FILENAME = "__init__.py"


def create_directory_if_not_exists(directory):
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except OSError:
            raise
        else:
            logger = logging.getLogger(__name__)
            logger.info("Directory: '{directory}' was not found, creating it now.".format(directory=directory))


def create_file_if_not_exists(file_name):
    directory = os.path.dirname(file_name)
    create_directory_if_not_exists(directory)
    
    if not os.path.isfile(file_name):
        try:
            with open(file_name, 'a+'):
                os.utime(file_name, None)
        except OSError:
            raise
        else:
            logger = logging.getLogger(__name__)
            logger.info("File: '{file}' was not found, creating it now.".format(file=file_name))


def create_python_package_if_not_exists(working_directory, package_name):
    package_directory = os.path.join(working_directory, package_name)
    create_directory_if_not_exists(package_directory)
    
    package_file = os.path.join(package_directory, PACKAGE_INIT_FILENAME)
    create_file_if_not_exists(package_file)
