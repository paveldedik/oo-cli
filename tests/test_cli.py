from datetime import UTC
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from oo_cli.cli import UsageError, _params, main
from oo_cli.config import Config, ConfigError
from oo_cli.timeutil import TimeError, to_micros


def test_query_parameters_accept_both_spellings() -> None:
    assert _params(["--folder=default", "--size", "10"]) == [("folder", "default"), ("size", "10")]


def test_a_flag_without_a_value_is_true() -> None:
    assert _params(["--enabled"]) == [("enabled", "true")]


def test_a_stray_positional_is_an_error() -> None:
    with pytest.raises(UsageError):
        _params(["folder"])


def test_token_is_sent_as_basic_auth() -> None:
    config = Config.from_env({"OO_TOKEN": "dXNlcjp0b2tlbg=="})
    assert config.authorization == "Basic dXNlcjp0b2tlbg=="


def test_a_token_naming_its_own_scheme_is_left_alone() -> None:
    assert Config.from_env({"OO_TOKEN": "Bearer abc"}).authorization == "Bearer abc"


def test_user_and_password_are_encoded() -> None:
    assert Config.from_env({"OO_USER": "user", "OO_PASSWORD": "token"}).authorization == (
        "Basic dXNlcjp0b2tlbg=="
    )


def test_half_a_credential_is_an_error() -> None:
    with pytest.raises(ConfigError):
        Config.from_env({"OO_USER": "user"})


def test_defaults_do_not_need_the_environment() -> None:
    config = Config.from_env({})
    assert (config.endpoint, config.org, config.authorization, config.cookie) == (
        "http://localhost:5080",
        "default",
        None,
        None,
    )


def test_a_gateway_cookie_is_taken_as_it_was_pasted() -> None:
    pasted = "AWSELBAuthSessionCookie-0=one; AWSELBAuthSessionCookie-1=two"
    assert Config.from_env({"OO_COOKIE": pasted}).cookie == pasted


@pytest.mark.parametrize(
    "value,micros",
    [
        ("1758196800", 1758196800_000_000),
        ("1758196800123", 1758196800123_000),
        ("1758196800123456", 1758196800123456),
        ("2026-09-18T12:00:00+00:00", 1789732800_000_000),
    ],
)
def test_timestamps_become_microseconds(value: str, micros: int) -> None:
    assert to_micros(value) == micros


def test_offsets_are_relative_to_now() -> None:
    from datetime import datetime

    now = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)
    assert to_micros("-15m", now=now) == to_micros("now", now=now) - 15 * 60 * 1_000_000


def test_nonsense_time_is_an_error() -> None:
    with pytest.raises(TimeError):
        to_micros("yesterday")


def test_a_negative_offset_is_not_read_as_an_option() -> None:
    from oo_cli.cli import _glue_offsets

    assert _glue_offsets(["search", "--from", "-30m", "--to", "now"]) == [
        "search",
        "--from=-30m",
        "--to",
        "now",
    ]


def test_the_skill_command_needs_no_endpoint(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    # It must work with nothing configured, before anyone has a token.
    monkeypatch.delenv("OO_TOKEN", raising=False)
    assert main(["skill", "install", "--dir", str(tmp_path)]) == 0
    assert (tmp_path / "openobserve" / "SKILL.md").is_file()
    assert main(["skill", "install", "--dir", str(tmp_path)]) == 1
