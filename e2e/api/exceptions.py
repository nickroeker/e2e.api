"""Exceptions raised by e2e.api."""

import requests


class RestApiException(Exception):
    """Base exception for REST API errors"""


class UnexpectedStatusError(RestApiException):
    """Raised when REST API calls return with an unexpected status code.

    Args:
        response: Response from which the status came.
        msg: Optional additional message explaining the details of the error.
    """

    def __init__(self, response: requests.Response, msg: str = ""):
        super().__init__(msg)
        self.msg = msg
        self.status_code = response.status_code  # type: int
        self.response = response

    def __str__(self) -> str:
        return self.msg


class IncompleteRequestError(RestApiException):
    """Raised when a request was not completed, for any reason."""
