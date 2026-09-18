# oo

A small CLI for the OpenObserve HTTP API. Commands are a transcription of the API rather
than a model of it: `oo get dashboards` is `GET /api/{org}/dashboards`, and anything the
CLI does not know about is still reachable with `oo api`.

```bash
oo get dashboards
oo get alerts --folder default           # GET /api/v2/{org}/alerts?folder=default
oo get streams/app_logs
oo post alerts -f alert.json
oo put dashboards/0194f0e1 -d @- < dashboard.json
oo delete alerts/7

oo search --sql "select * from default limit 10" --from -30m
oo api GET /api/default/prometheus/api/v1/query --query "up"
```

Any `--name value` or `--name=value` the CLI does not define becomes a query parameter.
`-d` takes a literal body, `@file` or `@-` for stdin; `-f file` is shorthand for `-d @file`.
Output is pretty-printed JSON on stdout, errors on stderr, exit code 1 on HTTP >= 400 and
2 on a bad command.

Times accept `now`, an offset (`-15m`, `-2h`, `-7d`), an epoch timestamp in seconds,
milliseconds or microseconds, or an ISO 8601 datetime (local time when it carries no zone).

## Install

```bash
uv tool install openobserve-cli     # installs the `oo` command
uvx openobserve-cli get streams     # or run it without installing anything
```

The command is `oo`; `openobserve-cli` is the same command under the distribution's
name, which is what makes the `uvx` one-liner work. From a checkout: `uv sync` and
then `uv run oo --help`.

## Configuration

Everything comes from the environment:

| Variable                  | Default                 | Meaning                                     |
|---------------------------|-------------------------|---------------------------------------------|
| `OO_ENDPOINT`             | `http://localhost:5080` | base URL                                    |
| `OO_ORG`                  | `default`               | organization                                |
| `OO_TOKEN`                | —                       | base64 of `email:token`, sent as basic auth |
| `OO_USER` / `OO_PASSWORD` | —                       | the same credential spelled out             |
| `OO_TIMEOUT`              | `60`                    | request timeout in seconds                  |
| `OO_LOGIN_PATH`           | `/cli-login`            | where the login helper is mounted           |
| `OO_HOME`                 | `~/.oo`                 | where the session file lives                |

`--endpoint`, `--org` and `--timeout` override the corresponding variable.

## When something authenticates in front of OpenObserve

Plenty of deployments put OpenObserve behind a gateway that authenticates users itself: an
AWS ALB with an `authenticate-oidc` action, oauth2-proxy, an identity-aware proxy. Such a
gateway takes nothing but its own session cookie, which it issues to a browser at the end
of an interactive login — no API token gets past it, and a CLI cannot run that flow on its
own, because the flow's nonce belongs to whoever started it and the cookie ends up in the
browser.

What a browser will do is send the cookie to anything behind the gateway. So deploy
[`deploy/login-helper.yaml`](deploy/login-helper.yaml) there, route one path to it, and:

```bash
oo auth login     # opens a tab in the browser you already have signed in
oo auth status
oo auth logout
```

The helper reads the cookie off its own request and redirects the browser to a loopback
port the CLI is listening on; the cookie is stored in `~/.oo/session.json` (0600) and
replayed on every request to that endpoint. The redirect target is always `127.0.0.1` and
only its port comes from the request, so the cookie cannot go anywhere but back to the
machine the browser runs on. Cookies whose name the helper does not recognize stay behind —
set `COOKIE_PATTERN` on the helper to match your gateway's.

If the helper is not deployed, `oo auth login --cookie "<Cookie header>"` takes the same
cookie pasted out of the browser's devtools, and a request that hits the gateway without a
session says so instead of failing on a page of HTML.

The gateway is orthogonal to OpenObserve's own authentication: the cookie gets you through
the door, `OO_TOKEN` still identifies you to OpenObserve.

## v1 and v2

Where an endpoint exists in both versions, v2 is used; there is no version switch. The CLI
reads the instance's own OpenAPI document (`/api-doc/openapi.json`) to decide, so it follows
whatever is deployed. The document is cached per endpoint under `~/.cache/oo-cli` for a week.

```bash
oo spec paths alerts     # list endpoints and their methods
oo spec refresh          # refetch after an OpenObserve upgrade
```

Without a reachable spec the CLI falls back to v1, except for `alerts`, `folders` and
`reports`, the three resources that have a v2 in OpenObserve 0.91.

## Development

```bash
uv sync
uv run pytest
pre-commit install     # ruff, mypy and conventional commit messages
```
