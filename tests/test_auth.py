import json
import webbrowser
from collections.abc import Callable
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit
from urllib.request import urlopen

import pytest

from oo_cli import auth, session

LOGIN_PATH = "/cli-login"


@pytest.fixture(autouse=True)
def oo_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("OO_HOME", str(tmp_path))
    return tmp_path


def _browser(**params: str) -> Callable[[str], bool]:
    """Stand in for the browser: whatever the helper behind the gateway redirects to."""

    def open_url(url: str) -> bool:
        query = parse_qs(urlsplit(url).query)
        answer = {"state": query["state"][0], **params}
        query_string = "&".join(f"{k}={quote(v)}" for k, v in answer.items())
        _swallow(f"http://127.0.0.1:{query['port'][0]}/callback?{query_string}")
        return True

    return open_url


def _swallow(url: str) -> None:
    from urllib.error import HTTPError

    try:
        urlopen(url)  # noqa: S310 - the test's own loopback server
    except HTTPError:
        pass


def test_the_browser_hands_over_every_cookie_the_gateway_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        webbrowser,
        "open",
        _browser(c0="AWSELBAuthSessionCookie-0=one", c1="AWSELBAuthSessionCookie-1=two/is+base64="),
    )

    cookies = auth.login("https://monitoring.example", LOGIN_PATH, timeout=10)

    assert cookies == {
        "AWSELBAuthSessionCookie-0": "one",
        "AWSELBAuthSessionCookie-1": "two/is+base64=",
    }


def test_the_cli_does_not_care_what_the_gateway_calls_its_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(webbrowser, "open", _browser(c0="_oauth2_proxy=abc"))
    cookies = auth.login("https://monitoring.example", LOGIN_PATH, timeout=10)
    assert cookies == {"_oauth2_proxy": "abc"}


def test_a_reply_with_the_wrong_state_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    def open_url(url: str) -> bool:
        port = parse_qs(urlsplit(url).query)["port"][0]
        _swallow(f"http://127.0.0.1:{port}/callback?state=elsewhere&c0=name%3Done")
        return True

    monkeypatch.setattr(webbrowser, "open", open_url)
    with pytest.raises(auth.LoginError, match="no response"):
        auth.login("https://monitoring.example", LOGIN_PATH, timeout=1)


def test_an_error_from_the_helper_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(webbrowser, "open", _browser(error="no session cookie"))
    with pytest.raises(auth.LoginError, match="no session cookie"):
        auth.login("https://monitoring.example", LOGIN_PATH, timeout=10)


def test_a_browser_that_will_not_open_says_which_url_to_visit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(webbrowser, "open", lambda url: False)
    with pytest.raises(auth.LoginError, match="cli-login"):
        auth.login("https://monitoring.example", LOGIN_PATH, timeout=10)


def test_a_pasted_cookie_header_is_read_as_it_comes() -> None:
    assert auth.parse_cookies("a=1; b=two=2  ") == {"a": "1", "b": "two=2"}


def test_a_paste_without_a_pair_is_an_error() -> None:
    with pytest.raises(auth.LoginError):
        auth.parse_cookies("just-a-value")


def test_a_session_is_stored_per_endpoint_and_only_for_the_user(oo_home: Path) -> None:
    session.save("https://one.example", {"AWSELBAuthSessionCookie-0": "a"})
    session.save("https://two.example", {"AWSELBAuthSessionCookie-0": "b"})

    assert session.load("https://one.example") == {"AWSELBAuthSessionCookie-0": "a"}
    assert session.load("https://missing.example") == {}
    assert oo_home.joinpath("session.json").stat().st_mode & 0o777 == 0o600

    assert session.clear("https://one.example") is True
    assert session.load("https://one.example") == {}
    assert json.loads(oo_home.joinpath("session.json").read_text()).keys() == {
        "https://two.example"
    }


def test_the_cookie_header_is_stable() -> None:
    assert session.header({"AWSELBAuthSessionCookie-1": "b", "AWSELBAuthSessionCookie-0": "a"}) == (
        "AWSELBAuthSessionCookie-0=a; AWSELBAuthSessionCookie-1=b"
    )
