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

Everything comes from the environment. Nothing is required: with no variables set the
CLI talks to `http://localhost:5080` as an anonymous user, which is what a port-forward
to a local OpenObserve looks like.

| Variable                  | Required                        | Default                 | Meaning                                       |
|---------------------------|---------------------------------|-------------------------|-----------------------------------------------|
| `OO_ENDPOINT`             | optional                        | `http://localhost:5080` | base URL                                      |
| `OO_ORG`                  | optional                        | `default`               | organization                                  |
| `OO_TOKEN`                | to reach anything but `/healthz`| —                       | base64 of `email:token`, sent as basic auth   |
| `OO_USER` / `OO_PASSWORD` | instead of `OO_TOKEN`           | —                       | the same credential spelled out               |
| `OO_COOKIE`               | when a gateway guards the host  | —                       | `Cookie` header, sent verbatim                |
| `OO_TIMEOUT`              | optional                        | `60`                    | request timeout in seconds                    |

`--endpoint`, `--org` and `--timeout` override the corresponding variable.

## When something authenticates in front of OpenObserve

Plenty of deployments put OpenObserve behind a gateway that authenticates users itself:
an AWS ALB with an `authenticate-oidc` action, oauth2-proxy, an identity-aware proxy.
Such a gateway takes nothing but its own session cookie, which it issues to a browser
at the end of an interactive login — no API token gets past it, and a CLI cannot run
that flow on its own.

So hand it the cookie your browser already has. In devtools, Network tab, take the
`Cookie` header off any request to that host (or Application, Cookies) and:

```bash
export OO_COOKIE="AWSELBAuthSessionCookie-0=...; AWSELBAuthSessionCookie-1=..."
```

It is sent verbatim, so any gateway's cookie works, whatever it calls it. A request
that hits the gateway without one says so instead of failing on a page of HTML. The
cookie expires on the gateway's schedule — an ALB session lasts 7 days by default.

The gateway is orthogonal to OpenObserve's own authentication: the cookie gets you
through the door, `OO_TOKEN` still identifies you to OpenObserve.

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

## Skill for agents

The CLI carries a skill for coding agents: how the commands map onto the API, what the
bodies look like, and a reference for every endpoint, written from an instance's own
OpenAPI document. It installs itself.

```bash
oo skill install            # -> ~/.agents/skills/openobserve
oo skill update             # after upgrading the CLI
```

`--dir` puts it wherever your agent looks (`oo skill install --dir ~/.claude/skills`, or
`--dir .claude/skills` for a single project),
`--force` overwrites an existing copy, and `oo skill path` prints the bundled original.
Without installing anything: `uvx openobserve-cli skill install`.

The files are also plain Markdown in `skills/openobserve`, so any agent that reads
Markdown can be pointed straight at `SKILL.md`.

## Development

```bash
uv sync
uv run pytest
pre-commit install     # ruff, mypy and conventional commit messages
```
