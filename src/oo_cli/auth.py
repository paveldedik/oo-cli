"""`oo auth login`: pick up the session cookie of an authenticating gateway.

Some deployments put OpenObserve behind a gateway that authenticates users itself —
an AWS ALB with an `authenticate-oidc` action, for instance. Such a gateway accepts
nothing but its own session cookie and issues it only to a browser at the end of the
OIDC flow, so a CLI cannot authenticate on its own: the flow's nonce belongs to
whoever started it, and the cookie ends up in the browser.

What a browser will do is send that cookie to anything behind the gateway. So the
deployment mounts a small endpoint there (`deploy/alb-oidc-login/`, path configurable
with OO_LOGIN_PATH) which reads the cookie off its own request and redirects the
browser to the loopback port this module listens on. No browser automation, no
reading of browser profiles, and it works with whichever browser the user already
has open and signed in.
"""

from __future__ import annotations

import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote, urlsplit

DEFAULT_TIMEOUT = 180.0


class LoginError(Exception):
    pass


def login(endpoint: str, login_path: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, str]:
    """Open the login URL in the running browser and wait for the cookies to come back."""
    state = secrets.token_hex(16)
    server = _CallbackServer(state)
    url = f"{endpoint}{login_path}?port={server.port}&state={quote(state)}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        if not webbrowser.open(url):
            raise LoginError(f"could not open a browser, visit this URL yourself:\n  {url}")
        print(f"Waiting for the browser to come back from {urlsplit(endpoint).netloc} ...")
        if not server.done.wait(timeout):
            raise LoginError(
                f"no response within {timeout:.0f}s; is {endpoint}{login_path} deployed?"
            )
    finally:
        server.shutdown()
        server.server_close()

    if server.error:
        raise LoginError(server.error)
    if not server.cookies:
        raise LoginError("the browser came back without a session cookie")
    return server.cookies


def parse_cookies(text: str) -> dict[str, str]:
    """Read a Cookie header the way a browser's devtools hands it over."""
    cookies = {}
    for part in text.strip().strip(";").split(";"):
        name, separator, value = part.strip().partition("=")
        if separator and name:
            cookies[name.strip()] = value.strip()
    if not cookies:
        raise LoginError("expected cookies as name=value, separated by semicolons")
    return cookies


class _CallbackServer(HTTPServer):
    def __init__(self, state: str) -> None:
        super().__init__(("127.0.0.1", 0), _CallbackHandler)
        self.state = state
        self.cookies: dict[str, str] = {}
        self.error: str | None = None
        self.done = threading.Event()

    @property
    def port(self) -> int:
        return self.server_address[1]


class _CallbackHandler(BaseHTTPRequestHandler):
    server: _CallbackServer

    def do_GET(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        url = urlsplit(self.path)
        if url.path != "/callback":
            self._respond(404, "<p>Not found.</p>")
            return

        params = parse_qs(url.query)
        if params.get("state", [""])[0] != self.server.state:
            self._respond(400, "<p>Stale login attempt. Run <code>oo auth login</code> again.</p>")
            return

        if "error" in params:
            self.server.error = params["error"][0]
            self._respond(400, "<p>Login failed. Back to the terminal.</p>")
            self.server.done.set()
            return

        # The helper sends the cookies it found as c0, c1, ... each a whole name=value
        # pair, so the CLI never has to know what the gateway calls them.
        cookies = {}
        for index in range(16):
            pair = params.get(f"c{index}", [""])[0]
            if not pair:
                break
            name, separator, value = pair.partition("=")
            if separator:
                cookies[name] = value
        self.server.cookies = cookies
        self._respond(200, "<p>Signed in. You can close this tab.</p>")
        self.server.done.set()

    def _respond(self, status: int, body: str) -> None:
        # replaceState keeps the cookie out of the browser's history and address bar.
        page = (
            "<!doctype html><meta charset=utf-8><title>oo</title>"
            "<body style='font:16px system-ui;margin:4rem auto;max-width:30rem'>"
            f"{body}<script>history.replaceState({{}},'','/')</script>"
        ).encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def log_message(self, *args: object) -> None:
        """Keep the request log off the terminal; the URL carries the cookie."""
