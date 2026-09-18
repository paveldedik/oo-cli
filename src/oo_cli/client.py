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
                method.upper(), path, params=params, content=body, headers=headers
            )
        except httpx.ConnectError as exc:
            raise OOError(f"{self.config.endpoint} is unreachable: {exc}\n{_UNREACHABLE_HINT}") from exc
        except httpx.HTTPError as exc:
            raise OOError(f"request to {self.config.endpoint}{path} failed: {exc}") from exc

        _reject_oidc_gate(response)
        if response.status_code >= 400:
            raise HTTPError(response)
        return response

    def json(self, method: str, path: str, **kwargs: Any) -> Any:
        return self.request(method, path, **kwargs).json()


_UNREACHABLE_HINT = (
    "Start the port-forward first:\n"
    "  kubectl -n openobserve port-forward svc/openobserve 5080:5080"
)

_OIDC_HINT = (
    "The endpoint sits behind the Entra ID OIDC gate on the ALB, which only accepts its own\n"
    "session cookie — no token gets past it. Point the CLI at a port-forward instead:\n"
    "  kubectl -n openobserve port-forward svc/openobserve 5080:5080\n"
    "  export OO_ENDPOINT=http://localhost:5080"
)


def _reject_oidc_gate(response: httpx.Response) -> None:
    """Turn the ALB's redirect to Entra into an explanation instead of a parse error."""
    location = response.headers.get("location", "")
    if response.is_redirect and "login.microsoftonline.com" in location:
        raise OOError(f"{response.request.url} is gated by Entra ID\n{_OIDC_HINT}")
    if "text/html" in response.headers.get("content-type", "") and "microsoft" in response.text.lower():
        raise OOError(f"{response.request.url} returned a Microsoft login page\n{_OIDC_HINT}")
