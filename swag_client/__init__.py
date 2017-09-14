import logging
from logging import NullHandler

from .exceptions import InvalidSWAGDataException

logging.getLogger(__name__).addHandler(NullHandler())

