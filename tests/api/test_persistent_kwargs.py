"""Tests to ensure that Session persistent kwargs are indeed persistent."""
from typing import Tuple
from unittest import mock

import pytest
import pytest_mock

from e2e.api import RestApi

ApiFixtureT = Tuple[RestApi, str]


@pytest.fixture(name="mock_request")
def mock_request_fixture(mocker: pytest_mock.MockFixture) -> mock.Mock:
    """Mocks and patches `requests.Session.request` and returns it."""
    mock_request = mocker.Mock()
    mocker.patch("requests.Session.request", mock_request)
    return mock_request


@pytest.fixture(name="rest_api")
def rest_api_fixture() -> ApiFixtureT:
    """Mocks and patches `requests.Session.request` and returns it."""
    url = "http://testurl.com/"
    api = RestApi(url, allow_redirects=False)
    return api, url


def test_persistent_kwargs_are_persistent(
    rest_api: ApiFixtureT, mock_request: mock.Mock
) -> None:
    """Verify that Session persistent kwargs are used implicitly."""
    api, url = rest_api
    api.get("")

    mock_request.assert_called_once_with(
        "GET", url, allow_redirects=False, timeout=10.0
    )


def test_persistent_kwargs_can_be_overridden(
    rest_api: ApiFixtureT, mock_request: mock.Mock
) -> None:
    """Verify that Session persistent kwargs can be overwritten.

    If a specific request specifies a kwarg which matches one which should
    be persistent, the request-specific value is used.
    """
    api, url = rest_api
    kwargs = {"allow_redirects": True, "timeout": 1234.5}
    api.get("", **kwargs)

    mock_request.assert_called_once_with("GET", url, **kwargs)
