"""Unit tests for RestApi magic methods."""
from e2e.api import RestApi


def test_repr_with_default_arguments() -> None:
    """Verify that repr contains the default timeout value."""
    url = "http://test.com/"
    api = RestApi(url)
    assert repr(api) == "e2e.api.api.RestApi('{}', timeout=10.0)".format(url)


def test_repr_with_additional_arguments() -> None:
    """Verify that repr contains additional persistent requests kwargs."""
    url = "http://test.com/"
    kwargs = {"allow_redirects": False, "timeout": 5.0}
    api = RestApi(url, **kwargs)

    # Since we sort the dict in __repr__ we need to do the same here.
    args = ("{}={}".format(k, repr(v)) for k, v in sorted(kwargs.items()))
    arg_str = ", ".join(args)
    assert repr(api) == "e2e.api.api.RestApi('{}', {})".format(url, arg_str)


def test_str_with_default_arguments() -> None:
    """Verify that the string returned by `str` is correct."""
    url = "http://test.com/"
    api = RestApi(url)
    assert str(api) == "RestApi({})".format(url)


def test_str_with_additional_arguments() -> None:
    """Verify that additional kwargs have no effect on `str`."""
    url = "http://test.com/"
    api = RestApi(url, timeout=20)
    assert str(api) == "RestApi({})".format(url)
