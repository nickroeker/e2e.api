"""Core API/Service wrapper functionality.

Provides,

- Session-based client which can persist cookies, headers, etc.
- User-friendly defaults useful for most APIs (10.0s timeout, fresh Sessions).
- Built-in status checking on a per-call basis.`
- Rich info on errors (underlying connection errors or status errors).

It is recommended to extend :class:`~api.RestApi` to add
:class:`e2e.api.endpoint.BasicEndpoint` instances as members, and to extend
any service-specific behaviour. For example,

- Default always-on status checking for each "Endpoint".
- Add an ``authenticate()`` method to the `RestApi` model.
- Provide additional helpers for your usage of the API.
- Extra health checks on responses (e.g. if a ``res.success` is ``False``).
"""

import json
import logging
import pprint
import re
import textwrap
from typing import Any
from typing import Dict
from typing import Optional
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

import requests

from . import base
from . import exceptions
from . import types

# TODO: Use e2e.common once available
# from e2e.common import check_type

LOGGER = logging.getLogger(__name__)

# TODO: See if we can glob the venv site-packages path for mypy on command
# line instead of static in the mypy.ini


class RestApi(base.ClassInfo):
    """Base class for REST API interfaces.

    This acts similar to a basic `requests.Session`, but adds features useful
    for automation such as:
        - Built-in status code checks with rich info on failure.
        - Default timeout for all requests, so nothing hangs by default.
        - Relative access from root URL, as is common when using REST APIs.
        - Additional logging (debug-level) for all requests made.

    Args:
        api_root: Root of the REST API to be used, e.g. 'http://myservice.com'
        session: Optional `requests.Session` to be used instead of a new one.
            You can use this to share one session across services, for example.
        persistent_kwargs: Optional :meth:`requests.Session.request` kwargs
            which will be used for all requests made by this RestApi.
    """

    class ExcFormatter:
        """Formatting helper for raised exceptions."""

        # TODO: This is all just terrible spaghetti
        EXC_INDENT_STEP = 4

        @classmethod
        def __get_textwrapper(cls, level: int) -> textwrap.TextWrapper:
            return textwrap.TextWrapper(
                width=79 - (cls.EXC_INDENT_STEP * level),
                break_long_words=True,
                replace_whitespace=False,
                drop_whitespace=False,
                break_on_hyphens=False,
                initial_indent=" " * (cls.EXC_INDENT_STEP * level),
                subsequent_indent=" " * (cls.EXC_INDENT_STEP * level),
            )

        @classmethod
        def format(cls, to_format: str, level: int = 0) -> str:
            """Gets an indented 79-char limit wrapped text body."""
            lines = cls.__get_textwrapper(level).wrap(str(to_format))
            if len(lines) >= 5:
                lines = lines[:5]
                lines += [" " * (cls.EXC_INDENT_STEP * level) + "<truncated>"]
            return "\n".join(lines)

    def __init__(
        self,
        api_root: str,
        timeout: float = 10.0,
        session: Optional[requests.Session] = None,
        **persistent_kwargs: Any
    ) -> None:
        self._session = session if session is not None else requests.Session()
        self._api_root = api_root
        self._persistent_kwargs = {"timeout": timeout, **persistent_kwargs}

    @property
    def url(self) -> str:
        """Gets the API's root URL.

        The URL will be normalized to match what a web browser would show. For
        details, see the :py:meth:`~api.RestApi.normalize_url` method.

        Returns:
            The API's root URL, normalized.
        """
        return RestApi.normalize_url(self._api_root)

    @property
    def headers(self) -> requests.structures.CaseInsensitiveDict:
        """Gets the headers for this API session."""
        headers = self._session.headers  # type: requests.structures.CaseInsensitiveDict
        return headers

    @property
    def cookies(self) -> requests.cookies.RequestsCookieJar:
        """Gets the current cookies for this API session."""
        cookies = self._session.cookies  # type: requests.cookies.RequestsCookieJar
        return cookies

    def request(
        self,
        method: str,
        uri: str,
        expected_status: Optional[types.StatusCodeOrSeq] = None,
        status_msg: Optional[str] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Base request method providing additional controls.

        Uses this `RestApi`'s default timeout for the request.

        Optionally checks the response's status code. If the status code does
        not match, an error is raised and the request/response details are
        logged.

        Additionally, all other exceptions from the `requests` package are
        re-raised with additional info.

        Args:
            method: HTTP method (``'GET'``, ``'PUT'``, ``'POST'``, etc.).
            uri: The relative API URI (eg. ``'/api/v2/comments'``).
            expected_status: The expected HTTP status codes. May be a single int
                or a tuple/list of ints.
            status_msg: Message to include if
                :exc:`~e2e.api.exceptions.UnexpectedStatusError` is raised.
            ``**kwargs``: Additional arguments to pass to the underlying
                :meth:`requests.Session.request`.

        Returns:
            The response.

        Raises:
            :exc:`e2e.api.exceptions.UnexpectedStatusError`: If the response
                status code does not match any given `expected_status`.
            :exc:`e2e.api.exceptions.IncompleteRequestError`: If an exception
                is raised while making the request.

        """
        exp_status_codes = (
            (expected_status,) if isinstance(expected_status, int) else expected_status
        )

        # Default persistent arguments + the desired kwargs for this request.
        args_to_pass: Dict[str, Any] = {**self._persistent_kwargs, **kwargs}

        LOGGER.debug("%s %s", method, uri)

        req_url = self._api_root + uri
        try:
            r = self._session.request(
                method, req_url, **args_to_pass
            )  # type: requests.Response
        except requests.exceptions.RequestException as e:
            # TODO: This is all just terrible spaghetti

            msg = "Exception raised on '{} {}'\n".format(method, req_url)
            msg += "    Request params (next line):\n        {}\n".format(
                args_to_pass if args_to_pass else ""
            )
            msg += "    Exception (next line):\n        {}: {}".format(
                base.ClassInfo.fqualname_of(e), str(e)
            )
            raise exceptions.IncompleteRequestError(msg) from e

        if exp_status_codes and r.status_code not in exp_status_codes:
            msg = "Unexpected status ({} {}) from '{} {}'\n".format(
                r.status_code, r.reason, method, req_url
            )
            msg += "    Request params (next line):\n        {}\n".format(
                pprint.pformat(args_to_pass, indent=4)
            )

            try:
                res_body = "JSON", RestApi.ExcFormatter.format(
                    pprint.pformat(r.json(), indent=4), 2
                )
            except json.JSONDecodeError:
                res_body = "text", RestApi.ExcFormatter.format(r.text, 2)

            msg += "    Response {} (next line):\n{}\n".format(*res_body)

            if status_msg:
                msg += "\tError Message: {}".format(status_msg)
            raise exceptions.UnexpectedStatusError(r, msg)

        return r

    def get(
        self,
        uri: str,
        expected_status: Optional[types.StatusCodeOrSeq] = None,
        status_msg: Optional[str] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Uses GET as the `method` for :py:meth:`~api.RestApi.request`."""
        return self.request("GET", uri, expected_status, status_msg, **kwargs)

    def post(
        self,
        uri: str,
        expected_status: Optional[types.StatusCodeOrSeq] = None,
        status_msg: Optional[str] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Uses POST as the `method` for :py:meth:`~api.RestApi.request`."""
        return self.request("POST", uri, expected_status, status_msg, **kwargs)

    def put(
        self,
        uri: str,
        expected_status: Optional[types.StatusCodeOrSeq] = None,
        status_msg: Optional[str] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Uses PUT as the `method` for :py:meth:`~api.RestApi.request`."""
        return self.request("PUT", uri, expected_status, status_msg, **kwargs)

    def patch(
        self,
        uri: str,
        expected_status: Optional[types.StatusCodeOrSeq] = None,
        status_msg: Optional[str] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Uses PATCH as the `method` for :py:meth:`~api.RestApi.request`."""
        return self.request("PATCH", uri, expected_status, status_msg, **kwargs)

    def delete(
        self,
        uri: str,
        expected_status: Optional[types.StatusCodeOrSeq] = None,
        status_msg: Optional[str] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Uses DELETE as the `method` for :py:meth:`~api.RestApi.request`."""
        return self.request("DELETE", uri, expected_status, status_msg, **kwargs)

    def options(
        self,
        uri: str,
        expected_status: Optional[types.StatusCodeOrSeq] = None,
        status_msg: Optional[str] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Uses OPTIONS as the `method` for :py:meth:`~api.RestApi.request`."""
        return self.request("OPTIONS", uri, expected_status, status_msg, **kwargs)

    @staticmethod
    def normalize_url(url: str) -> str:
        """Returns the given URL in a normalized form.

        The URL will be normalized to match what a modern web browser would
        show. For example, multiple slashes in the path will be consolidated
        and default ports will be removed (e.g. 443 for HTTPS).

        Args:
            url: The URL to normalize.

        Returns:
            The provided URL, normalized.
        """
        default_ports = [("https", 443), ("http", 80)]
        parsed = urlsplit(url)
        if (parsed.scheme, parsed.port) in default_ports:
            return urlunsplit(
                (
                    parsed.scheme,
                    parsed.hostname.lower(),
                    re.sub(r"/+", r"/", parsed.path),
                    parsed.query,
                    parsed.fragment,
                )
            )
        return urlunsplit(parsed)

    def __str__(self) -> str:
        return "{}({})".format(self.__class__.__qualname__, self.url)

    def __repr__(self) -> str:
        # Sort the dictionary so we get consistent results since not all
        # versions of python3 guarantee order.
        sorted_kwargs = sorted(self._persistent_kwargs.items())
        kwargs_str = ", ".join("{}={}".format(k, repr(v)) for k, v in sorted_kwargs)
        return "{}({}, {})".format(self.__fqualname__, repr(self.url), kwargs_str)
