"""
"""

from __future__ import absolute_import

# Default library imports
import logging
import os


def create_directory_if_not_exists(directory):
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except OSError:
            raise
        else:
            logger = logging.getLogger(__name__)
            logger.info("Directory: '{directory}' was not found, creating it now.".format(directory=directory))
