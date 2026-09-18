# Searching logs, metrics and traces

## `oo search`

```bash
oo search --sql "select * from k8s_logs where level = 'error'" --from -1h --size 50
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--sql` | required | the query; the stream is the table |
| `--from` | `-1h` | start; `now`, `-15m`, epoch s/ms/us, ISO 8601 |
| `--to` | `now` | end |
| `--size` | `100` | rows returned |
| `--offset` | `0` | rows skipped (`from` in the API) |
| `--type` | `logs` | `logs`, `metrics` or `traces` |

It posts to `/api/{org}/_search?type=<type>`:

```json
{"query": {"sql": "...", "start_time": 1789700000000000, "end_time": 1789703600000000,
           "from": 0, "size": 100}}
```

Any extra `--flag value` is appended to the query string, so `--validate true` or
`--is_ui_histogram true` reach the API unchanged.

## The SQL

DataFusion SQL over one stream at a time. What is specific to OpenObserve:

- `_timestamp` is the time column, in **microseconds**.
- `match_all('needle')` is full text search across the stream's full-text fields.
- `str_match(field, 'needle')` searches one field (case-sensitive; `str_match_ignore_case`
  where the build has it).
- `histogram(_timestamp)` buckets by time; `histogram(_timestamp, '30 second')` sets the
  width, and the alias you give it is the column name you get back.
- Field names with dots or dashes need double quotes: `"kubernetes.pod_name"`.
- `select *` on a wide stream is expensive - name the fields you need.

```sql
select histogram(_timestamp) as ts, count(*) as n from k8s_logs
where match_all('timeout') group by ts order by ts
```

```sql
select k8s_namespace_name as ns, count(*) as n from k8s_logs
where level = 'error' group by ns order by n desc limit 20
```

## The response

`hits` is the array of rows; `total` is the number of matching records, `size`/`from` echo
the pagination, and `took` is the milliseconds spent. `scan_size`, `scan_records` and
`idx_scan_size` say how much data the query actually touched - the honest measure of whether
a query was reasonable. `is_partial` with `new_start_time`/`new_end_time` means the range was
trimmed to the instance's `max_query_range`, so the result is not the whole window you asked
for. `function_error` carries VRL errors when `query_fn` was used.

```bash
oo search --sql "select * from k8s_logs limit 5" --from -10m | jq '.hits'
oo search --sql "select count(*) as n from k8s_logs" --from -24h | jq -r '.hits[0].n'
```

## The raw `POST /api/{org}/_search` body

Reach for `oo api` when `oo search` is not enough. `query.sql`, `query.start_time` and
`query.end_time` are required; times are microseconds and must not be zero.

| Field | Meaning |
|-------|---------|
| `query.from` / `query.size` | pagination |
| `query.track_total_hits` | exact `total` instead of an estimate |
| `query.quick_mode` | search only the first N fields - faster, incomplete rows |
| `query.histogram_interval` | bucket width for `histogram()`, in seconds |
| `query.timezone` | fixed offset (`"+02:00"`) applied to `histogram()` buckets |
| `query.query_fn` | a VRL function applied to every row before it is returned |
| `query.uses_zo_fn` | set when `query_fn` is a named function |
| `query.sampling_ratio` | 0.0-1.0, sample instead of scanning everything |
| `query.skip_wal` | ignore data not yet flushed from the write-ahead log |
| `query.streaming_output` / `streaming_id` | used with the streaming endpoints |
| `use_cache` / `clear_cache` | reuse or drop cached results |
| `timeout` | seconds |
| `regions` / `clusters` | restrict a multi-cluster search |
| `search_type`, `search_event_context` | tag the query's origin (`ui`, `dashboards`, `alerts`, `reports`, ...) |
| `encoding` | `base64` if `sql` is base64-encoded |

Query parameters: `type` (logs/metrics/traces), `validate=true` to have field names checked
against the stream schema before running, `is_ui_histogram`, `is_multi_stream_search`.

```bash
cat > /tmp/q.json <<'JSON'
{"query": {"sql": "select service, count(*) as n from k8s_logs group by service",
           "start_time": 1789700000000000, "end_time": 1789703600000000,
           "size": 100, "track_total_hits": true}}
JSON
oo api POST /api/default/_search --type logs -f /tmp/q.json
```

## Distinct values of a field

`GET /api/{org}/{stream}/_values` gives the top N values with counts - the cheap way to
answer "which services are in here" without grouping in SQL. `fields`, `size`, `from`,
`start_time` and `end_time` (microseconds) are required.

```bash
oo get k8s_logs/_values --fields level --size 10 \
  --start_time 1789700000000000 --end_time 1789703600000000
```

`filter=a=b` narrows it, `keyword=abc` matches substrings, `no_count=true` skips the counts.

## Context around one record

`GET /api/{org}/{stream}/_around?key=<_timestamp>&size=20` returns the records before and
after a timestamp - the "show me what happened around this error" view. The POST form takes
the whole record in the body instead of a key, which matches better when several records
share a timestamp.

## Long queries: search jobs

A query that would outlive the request timeout goes in as a job:

```bash
oo post search_jobs -d '{"query": {"sql": "...", "start_time": ..., "end_time": ...}}'
oo get search_jobs/<job_id>                    # status
oo get search_jobs/<job_id>/result --size 500  # when it has finished
oo post search_jobs/<job_id>/cancel            # stop a running one
oo post search_jobs/<job_id>/retry             # only for cancelled or failed jobs
oo delete search_jobs/<job_id>                 # removes the job and its stored results
```

## Partitions and streaming

`POST /api/{org}/_search_partition` splits a time range into partitions the instance thinks
are the right size; searching them one by one gives results sooner than one wide query. It
also reports `max_query_range`, which is the limit your range is silently trimmed to.

`_search_stream` and `_values_stream` push results over HTTP/2 as newline-delimited JSON.
The CLI prints what arrives, so add `--raw` and pipe into `jq -c`.

## Patterns

`POST /api/{org}/streams/{stream}/patterns/extract` runs a search and returns the extracted
log patterns instead of the rows - a fast way to see the shape of a noisy stream.

## Search history and saved views

```bash
oo api POST /api/default/_search_history -d '{"start_time": ..., "end_time": ..., "size": 50}'
oo get savedviews            # named searches from the UI
oo get savedviews/<view_id>  # "data" is base64 of the view's own JSON
```

## Keeping searches cheap

Always bound the range, and let SQL do the aggregation - `count(*) group by` returns a
handful of rows where `select *` would stream millions. Wide ranges over a raw stream are
what actually hurts a shared instance: scanning weeks of logs to count them can exhaust its
memory, while the same question asked as an aggregate over an hour at a time costs nothing.
Check `scan_records` in the response when in doubt, and prefer `_values` over `select
distinct`.
