"""Base endpoint classes provided by e2e.api."""

from typing import Any
from typing import Union
from urllib.parse import urljoin

import requests

from . import base
from .api import RestApi
from .decorators import jsonify


class BasicEndpoint(base.ClassInfo):
    """Establishes mappings to the basic functionality of a REST API endpoint.

    Args:
        api: The :class:`~e2e.api.RestApi` to use for performing requests.
        api_uri: The endpoint URL segment. When concatenated to an API Root it
            forms the full path to the resource.
        checked: Enables/disables the default status code checks, if defined.
            See :py:meth:`~endpoint.BasicEndpoint.set_status_checking()`.
    """

    # pylint: disable=arguments-differ
    __REQ_DOC_FMT = """Perform a {} request on this endpoint.

    See :py:meth:`~endpoint.BasicEndpoint.request` for more info.

    Args:
        uri_extension: Optional, extends the URI for this endpoint (e.g.
            for a specific resource).
        ``**kwargs``: Passed along to underlying :class:`~e2e.api.RestApi`
            request.
    """

    def __init__(self, api: RestApi, api_uri: str, checked: bool = True):
        self._api = api
        self._checked = checked
        # Ensure the URI starts with a slash
        str_uri = str(api_uri)
        self._uri = ("/" * (not str_uri.startswith("/"))) + str_uri

    @property
    def uri(self) -> str:
        """Returns this API's relative URI from endpoint setup."""
        return self._uri

    @property
    def url(self) -> str:
        """Returns the endpoint's full URL."""
        return urljoin(self._api.url, self.uri)

    def set_status_checking(self, checked: bool) -> None:
        """Set whether or not to automatically check status codes.

        Setting this to true will enable the default status checks, if defined
        by the :py:func:`~e2e.api.decorators.default_status_check` deacorator.

        See:
            :exc:`e2e.api.exceptions.UnexpectedStatusError`
        """
        self._checked = checked

    # TODO: Use Generic to make the typing more accurate for subclasses
    def extend(self, uri: str) -> "BasicEndpoint":
        """Clone this endpoint, but with an extended URI from this one."""
        return self.__class__(self._api, self._extend_uri(uri))

    def _extend_uri(self, uri_extension: Union[int, str] = "") -> str:
        slashify = self.uri.endswith("/")
        str_id = str(uri_extension)
        return (
            self.uri
            if not uri_extension
            else "{}/{}{}".format(self.uri, str_id, "/" * slashify).replace("//", "/")
        )

    def request(
        self, method: str, uri_extension: str = "", **kwargs: Any
    ) -> requests.Response:
        """Performs a request on this endpoint, optionally extending the URI.

        You may wish to "extend" the URI for gettings specific resources, e.g.::

            users = api.endpoint.BasicEndpoint(my_services, '/api/v1/users')
            users.get()        # All users: GET /api/v1/users
            users.get('1337')  # Specific user: GET /api/v1/users/1337

        Args:
            method: HTTP method to perform, e.g. 'GET'.
            resource_uri: Optional, extend the URI for this endpoint (e.g.
                for a specific ID).
            ``**kwargs``: Passed along to underlying :class:`~e2e.api.RestApi`
                request.
        """
        return self._api.request(method, self._extend_uri(uri_extension), **kwargs)

    def get(self, uri_extension: str = "", **kwargs: Any) -> requests.Response:
        return self.request("GET", uri_extension, **kwargs)

    def put(self, uri_extension: str = "", **kwargs: Any) -> requests.Response:
        return self.request("PUT", uri_extension, **kwargs)

    def post(self, uri_extension: str = "", **kwargs: Any) -> requests.Response:
        return self.request("POST", uri_extension, **kwargs)

    def patch(self, uri_extension: str = "", **kwargs: Any) -> requests.Response:
        return self.request("PATCH", uri_extension, **kwargs)

    def delete(self, uri_extension: str = "", **kwargs: Any) -> requests.Response:
        return self.request("DELETE", uri_extension, **kwargs)

    def options(self, uri_extension: str = "", **kwargs: Any) -> requests.Response:
        return self.request("OPTIONS", uri_extension, **kwargs)

    get.__doc__ = __REQ_DOC_FMT.format("GET")
    put.__doc__ = __REQ_DOC_FMT.format("PUT")
    post.__doc__ = __REQ_DOC_FMT.format("POST")
    patch.__doc__ = __REQ_DOC_FMT.format("PATCH")
    delete.__doc__ = __REQ_DOC_FMT.format("DELETE")
    options.__doc__ = __REQ_DOC_FMT.format("OPTIONS")


# TODO: Liskov says bad inheritance, I agree. Fix up this implementation.
class JsonEndpoint(BasicEndpoint):
    """Establishes mappings to the basic functionality of a JSON API endpoint.

    The get, post, etc. methods are converted to return a ResponseDict, which
    has dict-like access to the JSON response body but also includes a
    `response` member to preserve the data from a `requests.Response` object.

    Note:
        This is not strictly for jsonapi.org compliant services, and in fact
        does not provide any additional functionality for those.

    See:
        :py:class:`endpoint.BasicEndpoint` for more info on usage.
    """

    # TODO: The type warnings are valid, fix design.
    # TODO: Intercepting only `request` right now breaks most type-hinting

    # Intercept the base request ; rest are transformed
    request = jsonify(BasicEndpoint.request)  # type: ignore
