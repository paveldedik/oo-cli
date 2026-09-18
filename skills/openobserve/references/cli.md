# The `oo` command in full

## Shape

```
oo [--endpoint URL] [--org NAME] [--timeout SECONDS] [--raw] <command> ...
```

Global flags come **before** the command. `--version` prints the version and exits.

| Command | What it sends |
|---------|---------------|
| `oo get <resource>` | `GET /api/{org}/<resource>` (or the v2 path, see below) |
| `oo post <resource>` | `POST ...` |
| `oo put <resource>` | `PUT ...` |
| `oo patch <resource>` | `PATCH ...` |
| `oo delete <resource>` | `DELETE ...` |
| `oo api <METHOD> <path>` | exactly that path, no org inserted, no version guessing |
| `oo search --sql ...` | `POST /api/{org}/_search` with the body built for you |
| `oo spec paths [needle]` | nothing - prints the instance's own endpoint list |
| `oo spec refresh` | refetches `/api-doc/openapi.json` |

A resource is the path under the organization, slashes included:
`oo get streams/app_logs/schema` is `GET /api/{org}/streams/app_logs/schema`.

## Query parameters

Any `--name value` or `--name=value` the CLI does not define itself becomes a query
parameter. A flag with no value becomes `name=true`.

```bash
oo get alerts --folder default --enabled --page_size 20
#  -> GET /api/v2/{org}/alerts?folder=default&enabled=true&page_size=20
```

Parameter names are the API's own - `page_size`, `stream_type`, `delete_all` - not
prettified. A value that starts with `-` must use the `--name=value` form, otherwise
argparse reads it as another flag. `--from` and `--to` are glued automatically, so
`oo search --from -30m` works.

## Bodies

| Form | Meaning |
|------|---------|
| `-d '{"name": "x"}'` | literal body |
| `-d @alert.json` | read from a file |
| `-d @-` | read from stdin |
| `-f alert.json` | shorthand for `-d @alert.json` |

`-d` and `-f` together is an error. The body is sent as `application/json` verbatim - the
CLI does not validate or reshape it. The round trip that works for every resource:

```bash
oo get alerts/7 > alert.json
jq '.enabled = false' alert.json > patched.json
oo put alerts/7 -f patched.json
```

## Output and exit codes

- JSON responses are pretty-printed to stdout; `--raw` prints the body as it arrived
  (use it for CSV, NDJSON or anything you will pipe into a file).
- Errors go to stderr, so `oo get streams > streams.json` keeps stdout clean.
- Exit `0` on success, `1` on a transport error or HTTP >= 400 (the response body is
  printed to stderr), `2` on a usage, configuration or time-parsing error.

## v1, v2 and how a path is chosen

OpenObserve has been growing a `/api/v2/...` surface for a few resources - in 0.91 those are
`alerts`, `folders` and `reports`. There is no version flag; the CLI reads the instance's own
OpenAPI document and tries, in order:

1. `/api/v2/{org}/<resource>`
2. `/api/{org}/<resource>`
3. `/api/<resource>` - for the endpoints that sit outside an organization
   (`organizations`, `clusters`)

The candidate matching the most literal segments wins, so `oo get alerts/destinations` is
the v1 destinations endpoint and not v2's `alerts/{alert_id}` with "destinations" as an id.

The document is cached per endpoint under `~/.cache/oo-cli/spec-<hash>.json` for seven days.
`oo spec refresh` refetches it; do that after an OpenObserve upgrade. With no reachable spec
the CLI falls back to v1 for everything except `alerts`, `folders` and `reports`.

`oo spec paths <needle>` is the authoritative answer to "does this instance have that
endpoint", and is cheap:

```bash
oo spec paths incidents
oo spec paths /v2/          # everything v2 on this instance
```

When the CLI prints `... is not in the spec, sending it anyway`, the request is still made -
but the resource name is usually a typo. Check with `oo spec paths` first.

## Authentication

`OO_TOKEN` is sent as `Authorization: Basic <token>`, where the token is the base64 of
`email:token` exactly as OpenObserve's UI shows it under Ingestion. If it already names a
scheme (`Bearer ...`) it is sent verbatim. `OO_USER` + `OO_PASSWORD` is the same credential
spelled out - the CLI base64-encodes the pair. Half a pair is a configuration error.

## Something authenticating in front of OpenObserve

A gateway that authenticates users itself - an ALB with an OIDC action, oauth2-proxy, an
identity-aware proxy - accepts nothing but its own session cookie, which it only issues to a
browser at the end of an interactive login. No API token gets past it, and a CLI cannot run
that flow.

Take the cookie from a browser that is already logged in (devtools, Network, the `Cookie`
header of any request to that host) and hand it over:

```bash
export OO_COOKIE="AWSELBAuthSessionCookie-0=...; AWSELBAuthSessionCookie-1=..."
```

It is sent verbatim, so any gateway's cookie works. `OO_TOKEN` is still needed: the cookie
gets you through the door, the token identifies you to OpenObserve. A request that reaches
the gateway without a valid cookie is refused with an explanation rather than a page of
login HTML.

Cookies expire on the gateway's schedule (an ALB session defaults to seven days). Never echo
the value into a terminal, a commit, or a chat message.

## Errors you will actually see

| Message | What it means |
|---------|---------------|
| `redirected to login.microsoftonline.com ...` | the gateway rejected the request; refresh `OO_COOKIE` |
| `401 Unauthorized` | `OO_TOKEN` missing, stale, or for another instance |
| `403 Forbidden` | the credential is valid but lacks the permission, or the endpoint is enterprise-only |
| `404 Not Found` on a plausible path | wrong org (`--org`), or the object id does not exist |
| `... is not in the spec` | wrong resource name - `oo spec paths <needle>` |
| `Connection refused` | nothing on `OO_ENDPOINT`; a port-forward may have died |
| `invalid character '<'`-style HTML in the body | you reached a login page, not the API |

## Local development against a cluster

When OpenObserve runs in Kubernetes, forward the service and point the CLI at it:

```bash
kubectl -n <namespace> port-forward svc/openobserve 5080:5080 &
export OO_ENDPOINT=http://localhost:5080
oo api GET /healthz
```

The port-forward dies with its shell; a sudden `Connection refused` usually means exactly
that and not an OpenObserve problem.
