=======
e2e.api
=======

Notice
------
``e2e.api`` is still in **active development** and should be treated as an
alpha package.

This project follows SemVer. It is expected that the first major release (1.x)
will differ in API functionality slightly from the alpha/beta track (0.x), but
most differences will be internal.

Python 3.5+ is currently required. No support for 2.x is ever planned since
it is soon to be unsupported. Earlier 3.x versions may be supported if someone
can wrangle the type-hinting out into stubs instead of with the source.

Please feel free to file any issues and suggestions even during the early
development phases.

========
Overview
========

Provides simplified and wrapped usage of the common `requests` package, focusing on,

- Session-based client which can get and store cookies
- Sane defaults for working with RESTful APIs (10.0 sec timeout, fresh Sessions)
- Work with relative URIs (e.g. '/api/v1/comments') versus concatenating with root URLS
- Built-in status checking, raising :py:class:`~e2e.api.exceptions.UnexpectedStatusError`
- Rich info on errors (underlying connection errors or status errors)

With ``requests``,

.. code-block:: python
    :name: With requests

    # requests: Don't forget the timeout on every request!
    import requests
    session = requests.Session()
    base_url = "http://foo.bar"

    # Source of error: Add '/' or not? Does base_url have an ending '/'?
    # Source of error: If you forget timeout=, then this could wait forever! (not good in an automation environment)
    session.options(base_url + '/api/version', timeout=2.0)
    session.get(base_url + '/api/version', timeout=2.0)

    # On error, all you know is status != 204, maybe more with pytest
    response = session.post(base_url + '/api/v1/data', json={'username': 'foobar'}, timeout=2.0)
    assert response.status_code == 204
    >>> E    AssertionError: 500 != 204


With ``e2e.api``,

.. code-block:: python
   :name: Using e2e.api

    from e2e.api import RestApi
    foo_api = RestApi("http://foo.bar")  # Sane timeout of 10.0 sec if not specified

    foo_api.options('/api/v1/version')
    foo_api.get('/api/v1/version')

    # Much more info on failure
    foo_api.post('/api/v1/data', json={'username': 'foobar'}, expected_status=204)
    >>> E   e2e.api.exceptions.UnexpectedStatusError: Unexpected status (500 Internal Server Error) from 'POST http://foo.bar/api/v1/data'
    >>> E       Request params (next line):
    >>> E           {'json': {'username': 'foobar'}}
    >>> E       Response JSON (next line):
    >>> E           {
    >>> E               "message": "A fatal error occurred, please try again later."
    >>> E               "error_id": "some.error.code.hw4gSD0"
    >>> E           }

Even simpler, custom :py:class:`e2e.api.RestApi <e2e.api.api.RestApi>` classes can be extended
with :py:class:`e2e.api.endpoint.BasicEndpoint` s.

.. code-block:: python
    :name: Using e2e.api.endpoint

    from e2e import api

    class MyApi(api.RestApi)
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.data = api.endpoint.BasicEndpoint(self, '/api/v1/data')
            self.version = api.endpoint.BasicEndpoint(self, '/api/v1/version')

    my_api = MyApi('http://foo.bar')
    my_api.version.options()
    my_api.version.get()
    my_api.data.post(json={'username': 'foobar'}, expected_status=204)
