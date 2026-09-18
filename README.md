# oo

A small CLI for the OpenObserve HTTP API. Commands are a transcription of the API rather
than a model of it: `oo get dashboards` is `GET /api/{org}/dashboards`, and anything the
CLI does not know about is still reachable with `oo api`.

## Install

```bash
uv tool install --from . oo-cli     # installs the `oo` binary
uv run oo --help                    # or just run it from the checkout
```

## Endpoint and credentials

Everything comes from the environment:

| Variable      | Default                 | Meaning                                       |
|---------------|-------------------------|-----------------------------------------------|
| `OO_ENDPOINT` | `http://localhost:5080` | base URL                                      |
| `OO_ORG`      | `default`               | organization                                  |
| `OO_TOKEN`    | —                       | base64 of `email:token`, sent as basic auth   |
| `OO_USER` / `OO_PASSWORD` | —           | the same credential spelled out               |
| `OO_TIMEOUT`  | `60`                    | request timeout in seconds                    |

`--endpoint`, `--org` and `--timeout` override the corresponding variable.

### Why the default endpoint is localhost

`https://monitoring.internal.skippay.dev` sits behind Entra ID OIDC on the ALB, and that
gate covers `/api/*` too. The ALB accepts nothing but its own session cookie, which is
issued to a browser at the end of an interactive login — no token or header gets past it.
So the CLI talks to a port-forward:

```bash
kubectl -n openobserve port-forward svc/openobserve 5080:5080
```

Requests that do hit the gated host fail with an explanation rather than a JSON parse error.

## Usage

```bash
oo get dashboards
oo get alerts --folder default           # GET /api/v2/{org}/alerts?folder=default
oo get streams/sp_metrics
oo post alerts -f alert.json
oo put dashboards/0194f0e1 -d @- < dashboard.json
oo delete alerts/7

oo search --sql "select * from cloudwatch_logs limit 10" --from -30m
oo api GET /api/default/prometheus/api/v1/query --query "up"
```

Any `--name value` or `--name=value` the CLI does not define becomes a query parameter.
`-d` takes a literal body, `@file` or `@-` for stdin; `-f file` is shorthand for `-d @file`.
Output is pretty-printed JSON on stdout, errors on stderr, exit code 1 on HTTP >= 400.

Times accept `now`, an offset (`-15m`, `-2h`, `-7d`), an epoch timestamp in seconds,
milliseconds or microseconds, or an ISO 8601 datetime (local time when it carries no zone).

### v1 and v2

Where an endpoint exists in both versions, v2 is used; there is no version switch. The CLI
reads the instance's own OpenAPI document (`/api-doc/openapi.json`) to decide, so it follows
whatever is deployed. The document is cached per endpoint under `~/.cache/oo-cli` for a week.

```bash
oo spec paths alerts     # list endpoints and their methods
oo spec refresh          # refetch after an OpenObserve upgrade
```

Without a reachable spec the CLI falls back to v1, except for `alerts`, `folders` and
`reports`, the three resources that have a v2 today.

## Development

```bash
uv sync
uv run pytest
```
