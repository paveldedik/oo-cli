import pytest

from oo_cli.cli import UsageError, _params
from oo_cli.config import Config, ConfigError
from oo_cli.timeutil import TimeError, to_micros


def test_query_parameters_accept_both_spellings():
    assert _params(["--folder=default", "--size", "10"]) == [("folder", "default"), ("size", "10")]


def test_a_flag_without_a_value_is_true():
    assert _params(["--enabled"]) == [("enabled", "true")]


def test_a_stray_positional_is_an_error():
    with pytest.raises(UsageError):
        _params(["folder"])


def test_token_is_sent_as_basic_auth():
    config = Config.from_env({"OO_TOKEN": "dXNlcjp0b2tlbg=="})
    assert config.authorization == "Basic dXNlcjp0b2tlbg=="


def test_a_token_naming_its_own_scheme_is_left_alone():
    assert Config.from_env({"OO_TOKEN": "Bearer abc"}).authorization == "Bearer abc"


def test_user_and_password_are_encoded():
    assert Config.from_env({"OO_USER": "user", "OO_PASSWORD": "token"}).authorization == (
        "Basic dXNlcjp0b2tlbg=="
    )


def test_half_a_credential_is_an_error():
    with pytest.raises(ConfigError):
        Config.from_env({"OO_USER": "user"})


def test_defaults_do_not_need_the_environment():
    config = Config.from_env({})
    assert (config.endpoint, config.org, config.authorization) == (
        "http://localhost:5080",
        "default",
        None,
    )


@pytest.mark.parametrize(
    "value,micros",
    [
        ("1758196800", 1758196800_000_000),
        ("1758196800123", 1758196800123_000),
        ("1758196800123456", 1758196800123456),
        ("2026-09-18T12:00:00+00:00", 1789732800_000_000),
    ],
)
def test_timestamps_become_microseconds(value, micros):
    assert to_micros(value) == micros


def test_offsets_are_relative_to_now():
    from datetime import datetime, timezone

    now = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
    assert to_micros("-15m", now=now) == to_micros("now", now=now) - 15 * 60 * 1_000_000


def test_nonsense_time_is_an_error():
    with pytest.raises(TimeError):
        to_micros("yesterday")


def test_a_negative_offset_is_not_read_as_an_option():
    from oo_cli.cli import _glue_offsets

    assert _glue_offsets(["search", "--from", "-30m", "--to", "now"]) == [
        "search",
        "--from=-30m",
        "--to",
        "now",
    ]
