"""SWAG exception classes"""


class InvalidSWAGDataException(Exception):
    pass


class SWAGException(Exception):
    pass


class InvalidSWAGBackendError(SWAGException, ImportError):
    pass


class MissingSWAGParameter(SWAGException):
    pass
