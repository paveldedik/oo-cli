import httpx
import pytest

from oo_cli.client import OOError, _reject_gateway


def _response(location):
    request = httpx.Request("GET", "https://monitoring.example/api/default/streams")
    return httpx.Response(302, headers={"location": location}, request=request)


def test_a_redirect_to_another_host_is_read_as_an_authenticating_gateway():
    with pytest.raises(OOError, match="oo auth login"):
        _reject_gateway(_response("https://login.microsoftonline.com/tenant/oauth2/v2.0/authorize"))


def test_a_redirect_within_the_endpoint_is_left_to_the_caller():
    _reject_gateway(_response("https://monitoring.example/web/"))


def test_a_relative_redirect_is_left_to_the_caller():
    _reject_gateway(_response("/web/"))
