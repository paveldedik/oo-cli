"""Endpoint, organization and credentials, all from the environment."""

from __future__ import annotations

import base64
import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_ENDPOINT = "http://localhost:5080"
DEFAULT_ORG = "default"
DEFAULT_TIMEOUT = 60.0
#: Where the login helper is mounted behind the gateway, see `oo auth login`.
DEFAULT_LOGIN_PATH = "/cli-login"


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    endpoint: str
    org: str
    authorization: str | None
    timeout: float
    login_path: str

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        endpoint: str | None = None,
        org: str | None = None,
        timeout: float | None = None,
    ) -> Config:
        values: Mapping[str, str] = os.environ if env is None else env
        return cls(
            endpoint=(endpoint or values.get("OO_ENDPOINT") or DEFAULT_ENDPOINT).rstrip("/"),
            org=org or values.get("OO_ORG") or DEFAULT_ORG,
            authorization=_authorization(values),
            timeout=timeout or float(values.get("OO_TIMEOUT") or DEFAULT_TIMEOUT),
            login_path=values.get("OO_LOGIN_PATH") or DEFAULT_LOGIN_PATH,
        )


def _authorization(env: Mapping[str, str]) -> str | None:
    """Build the Authorization header value.

    OO_TOKEN is the credential OpenObserve hands out for a service account (base64
    of "email:token"); it is sent as-is when it already names its scheme.
    OO_USER + OO_PASSWORD is the same thing spelled out.
    """
    token = env.get("OO_TOKEN")
    if token:
        token = token.strip()
        return token if " " in token else f"Basic {token}"

    user, password = env.get("OO_USER"), env.get("OO_PASSWORD")
    if user and password:
        return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
    if user or password:
        raise ConfigError("OO_USER and OO_PASSWORD have to be set together")
    return None
