---
name: openobserve
description: Query and manage OpenObserve from a terminal with the `oo` CLI - search logs, traces and metrics with SQL or PromQL, and read or change streams, dashboards, alerts, pipelines, functions and reports. Use for any task that mentions OpenObserve, an `oo` command, or an OpenObserve API path.
license: MIT
---

# OpenObserve from the command line

`oo` is a transcription of the OpenObserve HTTP API, not a model of it. One rule covers
almost everything:

```
oo <method> <resource>   ->   <METHOD> /api/{org}/<resource>
```

So `oo get dashboards` is `GET /api/default/dashboards`, and `oo delete alerts/7` is
`DELETE /api/v2/default/alerts/7`. Where an endpoint exists in two versions the CLI picks
v2; there is no version flag. Anything the rule does not reach is still one command away
with `oo api <METHOD> <path>`.

Install with `uv tool install openobserve-cli`, or run it without installing:
`uvx openobserve-cli get streams`.

## Start here

Check what you are pointed at before anything else - it is the difference between an empty
result and an empty instance:

```bash
oo api GET /healthz          # {"status":"ok"} - confirms it is an OpenObserve
oo get organizations         # confirms the credentials and lists the orgs you can use
oo get streams               # what data this org actually holds
```

Configuration is environment only:

| Variable                  | Required                          | Default                 |
|---------------------------|-----------------------------------|-------------------------|
| `OO_ENDPOINT`             | optional                          | `http://localhost:5080` |
| `OO_ORG`                  | optional                          | `default`               |
| `OO_TOKEN`                | to reach anything but `/healthz`  | -                       |
| `OO_USER` / `OO_PASSWORD` | instead of `OO_TOKEN`             | -                       |
| `OO_COOKIE`               | when a gateway guards the host    | -                       |
| `OO_TIMEOUT`              | optional                          | `60` (seconds)          |

`--endpoint`, `--org` and `--timeout` override the variables per command. Never print a
token or cookie value back to the user; keep it in the environment.

## The grammar

```bash
oo get alerts --folder default        # unknown --flags become query parameters
oo get streams/app_logs/schema        # slashes are path segments
oo post alerts -f alert.json          # -f file, -d '<literal>', -d @file, -d @-
oo put alerts/7 -d @- < alert.json    # body on stdin
oo --org other get streams            # global flags go before the verb
oo search --sql "select * from k8s_logs limit 10" --from -15m
oo api GET /api/default/prometheus/api/v1/query --query "up"
oo spec paths alerts                  # what this instance actually serves
```

- Output is pretty-printed JSON on stdout; errors on stderr. Pipe into `jq`.
- Exit code 1 on HTTP >= 400 (the response body is printed), 2 on a bad command.
- `--raw` prints the body unformatted, for CSV or a large export.
- Values starting with `-` need `--flag=value`; `--from` and `--to` are handled for you.

## Time

Every timestamp the API takes or returns is **epoch microseconds**. `oo search --from/--to`
and nothing else accepts friendly forms: `now`, an offset (`-15m`, `-2h`, `-7d`), an epoch
in seconds/milliseconds/microseconds, or ISO 8601 (local time when it carries no zone).
Elsewhere - `start_time` in a body, `_values`, alert history - pass microseconds:

```bash
python3 -c 'import time; print(int(time.time()*1_000_000))'
date -v-1H +%s000000        # macOS       (GNU: date -d '1 hour ago' +%s000000)
```

## Searching

`oo search` is the one command that is not a straight transcription: it wraps
`POST /api/{org}/_search` so the body does not have to be written by hand.

```bash
oo search --sql "select * from k8s_logs where level = 'error'" --from -1h --size 50
oo search --sql "select k8s_namespace_name, count(*) as n from k8s_logs
                 group by k8s_namespace_name order by n desc" --from -6h
oo search --type metrics --sql "select * from up" --from -5m
```

`--from` defaults to `-1h`, `--to` to `now`, `--size` to 100, `--type` to `logs`. The SQL is
DataFusion SQL: the stream is the table, `_timestamp` is microseconds, and full text lives in
`match_all('needle')`. Read `references/search.md` before writing anything more involved -
histograms, `_values`, `_around`, async search jobs and the raw `_search` body are all there.

Two habits that keep a search cheap on a busy instance: always bound the time range, and
aggregate in SQL rather than pulling rows and counting them locally. A wide range over a raw
stream can cost the instance far more memory than it costs you to type.

## Common tasks

| Question | Command |
|----------|---------|
| what is in this instance | `oo get streams`, then `oo get streams/<name>/schema` |
| errors in the last hour | `oo search --sql "select * from <stream> where level = 'error'" --from -1h` |
| how many, by service | `oo search --sql "select service, count(*) as n from <stream> group by service order by n desc" --from -6h` |
| which values does this field take | `oo get <stream>/_values --fields <field> --size 20 --start_time <us> --end_time <us>` |
| current value of a metric | `oo api GET /api/{org}/prometheus/api/v1/query --query '<promql>'` |
| which alerts exist, and are they on | `oo get alerts \| jq -r '.list[] \| "\(.enabled) \(.name)"'` |
| why an alert did not fire | `oo get alerts/history --alert_id <id> --start_time <us> --end_time <us>` |
| back up a dashboard | `oo get dashboards/<id> --folder <folder> > dashboard.json` |
| change one field of an object | read it, edit the JSON, `oo put <resource>/<id> -f patched.json` |
| does this instance have X | `oo spec paths <needle>` |

## Rules worth keeping

1. **Read before you write.** `PUT` replaces the whole object. Fetch it, edit that JSON,
   send it back - never hand-write a replacement from the docs.
2. **Dashboards need their `hash`.** `PUT dashboards/<id>` takes `?folder=<id>&hash=<hash>`
   from the object you just read; without it a concurrent edit is silently overwritten.
3. **Folders are ids, not names.** `--folder default` is the id of the default folder;
   any other folder is a ksuid you get from `oo get folders/<dashboards|alerts|reports>`.
4. **Deletes are permanent** and `oo delete streams/<name> --delete_all=true` takes the
   alerts and dashboards with it. Confirm with the user before any delete.
5. **Ask the spec, not your memory.** `oo spec paths <needle>` lists what the connected
   instance serves; `oo spec refresh` refetches it after an upgrade. Endpoint availability
   differs between OSS and enterprise builds - several alert and cipher endpoints answer
   "not supported" on OSS.
6. When a command says a path *is not in the spec*, the resource name is probably wrong -
   check with `oo spec paths` instead of retrying variations.

## References

| File | What is in it |
|------|---------------|
| `references/cli.md` | Full command grammar, v1/v2 resolution, the spec cache, gateways, error messages |
| `references/search.md` | `_search` body, SQL dialect, histograms, `_values`, `_around`, search jobs, patterns |
| `references/metrics.md` | PromQL instant/range queries, labels, series, metadata, metric ingestion |
| `references/alerts.md` | Alert model (v2), trigger and query conditions, destinations, templates, history, incidents |
| `references/dashboards.md` | Dashboards, panels, annotations, folders, scheduled reports |
| `references/streams.md` | Streams, schemas, settings, retention, ingestion endpoints, enrichment tables |
| `references/pipelines.md` | Pipelines (nodes and edges), VRL functions, actions |
| `references/admin.md` | Organizations, settings, users, roles, groups, service accounts, tokens, KV |
| `references/endpoints.md` | Every endpoint the API exposes, as the `oo` command that reaches it |
