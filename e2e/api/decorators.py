"""Decorators used internally for e2e.api."""

import functools
from typing import Any
from typing import Callable
from typing import Dict
from typing import TypeVar

import requests

from . import types


# Builtin wrapper, pylint: disable=too-few-public-methods
class ResponseDict(Dict[str, Any]):
    """Provides a dict-like wrapper for JSON responses.

    Though this is used as a regular dict, it also retains the original
    `requests.Response` object via the `response` member for getting status
    codes, headers, etc.
    """

    def __init__(self, raw_response: requests.Response) -> None:
        super().__init__(raw_response.json() if raw_response.content else {})
        self.response = raw_response


# FIXME: There's probably work to be done here for type correctness
def jsonify(responder: Callable[..., requests.Response]) -> Callable[..., ResponseDict]:
    """Converts a response to a :class:`~decorators.ResponseDict`.

    An empty server response will be treated as an empty dict instead (and the
    returned ResponseDict.response.content will be preserved as per `requests`).

    See Also:
        :class:`~e2e.api.decorators.ResponseDict`
    """

    @functools.wraps(responder)
    def func_wrapper(*args: Any, **kwargs: Any) -> ResponseDict:
        return ResponseDict(responder(*args, **kwargs))

    return func_wrapper


T_R = TypeVar("T_R", requests.Response, ResponseDict)


# FIXME: There's probably work to be done here for type correctness
def default_status_check(
    expected_status_codes: types.StatusCodeOrSeq,
) -> Callable[..., Callable[..., T_R]]:
    """Inserts a configurable status check into the request.

    The status check must be enabled in the implementing class via a truthy
    value on the `_checked` member.

    If the caller provides an expected status, the caller-specified status
    will entirely override this default.
    """

    def decorator(responder: Callable[..., T_R]) -> Callable[..., T_R]:
        @functools.wraps(responder)
        def func_wrapper(self: Any, *args: Any, **kwargs: Any) -> T_R:
            # FIXME: There should be a better way for this, one day.
            # Intentionally gross, pylint: disable=protected-access
            if self._checked and "expected_status" not in kwargs:
                kwargs["expected_status"] = expected_status_codes
            return responder(self, *args, **kwargs)

        return func_wrapper

    return decorator
