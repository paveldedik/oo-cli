"""Thin HTTP client for the OpenObserve API."""

from __future__ import annotations

from typing import Any

import httpx

from oo_cli.config import Config


class OOError(Exception):
    """Anything that should end the process with a message and a non-zero code."""


class HTTPError(OOError):
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        super().__init__(f"{response.status_code} {response.reason_phrase} {response.request.url}")


class Client:
    def __init__(self, config: Config) -> None:
        self.config = config
        headers = {"Accept": "application/json"}
        if config.authorization:
            headers["Authorization"] = config.authorization
        if config.cookie:
            headers["Cookie"] = config.cookie
        self._http = httpx.Client(
            base_url=config.endpoint,
            headers=headers,
            timeout=config.timeout,
            follow_redirects=False,
        )

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self._http.close()

    def request(
        self,
        method: str,
        path: str,
        params: list[tuple[str, str]] | None = None,
        body: bytes | None = None,
    ) -> httpx.Response:
        headers = {"Content-Type": "application/json"} if body is not None else None
        try:
            response = self._http.request(
                method.upper(),
                path,
                # A tuple, because httpx types its list of pairs invariantly.
                params=tuple(params) if params is not None else None,
                content=body,
                headers=headers,
            )
        except httpx.ConnectError as exc:
            raise OOError(
                f"{self.config.endpoint} is unreachable: {exc}\n{_UNREACHABLE_HINT}"
            ) from exc
        except httpx.HTTPError as exc:
            raise OOError(f"request to {self.config.endpoint}{path} failed: {exc}") from exc

        _reject_gateway(response)
        if response.status_code >= 400:
            raise HTTPError(response)
        return response

    def json(self, method: str, path: str, **kwargs: Any) -> Any:
        return self.request(method, path, **kwargs).json()


_UNREACHABLE_HINT = "Set OO_ENDPOINT to a reachable OpenObserve, or start your port-forward."

_GATEWAY_HINT = (
    "Something in front of OpenObserve is authenticating users itself and only takes its\n"
    "own session cookie, which no API token replaces. Copy the Cookie header out of the\n"
    "browser that is signed in (devtools, Network tab) and pass it along:\n"
    '  export OO_COOKIE="AWSELBAuthSessionCookie-0=...; AWSELBAuthSessionCookie-1=..."'
)


def _reject_gateway(response: httpx.Response) -> None:
    """Explain a redirect to an identity provider instead of leaving a parse error behind."""
    location = response.headers.get("location", "")
    if not response.is_redirect or not location.startswith(("http://", "https://")):
        return
    if httpx.URL(location).host == response.request.url.host:
        return
    raise OOError(
        f"{response.request.url} redirected to {httpx.URL(location).host}\n{_GATEWAY_HINT}"
    )
