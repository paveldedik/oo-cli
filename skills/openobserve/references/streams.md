# Streams: schema, settings and ingestion

A stream is a table. Logs, metrics and traces are all streams, told apart by `type`, which
defaults to `logs` everywhere.

## What is here

```bash
oo get streams                          # logs
oo get streams --type metrics
oo get streams --type traces
oo get streams --keyword k8s --limit 20 --offset 0 --sort name
```

Each entry carries `name`, `stream_type`, `storage_type`, `total_fields`, `settings` and
`stats`: `doc_num`, `doc_time_min`/`doc_time_max` (microseconds), `storage_size`,
`compressed_size` and `index_size` (megabytes, as the UI shows them), `file_num`.
The response is `{"list": [...], "total": n}`.

```bash
# the streams that actually hold something, largest first
oo get streams | jq -r '.list[] | "\(.stats.storage_size|floor)MB \(.name)"' | sort -rn
# is this stream still receiving data?
oo get streams | jq -r '.list[] | select(.name=="k8s_logs") | .stats.doc_time_max'
```

## Schema

```bash
oo get streams/k8s_logs/schema
oo get streams/k8s_logs/schema --keyword pod --limit 50
oo get streams/<metric>/schema --type metrics
```

Read the schema before writing SQL: it is the list of columns, with types, and it is the
difference between a working query and `field not found`. `--keyword` filters the field list
on a wide stream.

## Settings

```bash
# there is no GET on a single stream - read the settings out of the list
oo get streams --keyword k8s_logs | jq '.list[] | select(.name == "k8s_logs") | .settings'
oo put streams/k8s_logs/settings -d '{"data_retention": 30}'
```

`PUT .../settings` is a patch, not a replacement, and list-valued settings take
`{"add": [...], "remove": [...]}`:

```json
{
  "data_retention": 30,
  "max_query_range": 24,
  "full_text_search_keys": {"add": ["message"], "remove": []},
  "partition_keys": {"add": [{"field": "namespace"}], "remove": []},
  "index_fields": {"add": ["trace_id"], "remove": []},
  "bloom_filter_fields": {"add": ["user_id"], "remove": []},
  "defined_schema_fields": {"add": ["level", "message"], "remove": []}
}
```

| Setting | What it does |
|---------|--------------|
| `data_retention` | days before data is dropped |
| `extended_retention_days` | keep specific windows longer: `{"add": [{"start": <us>, "end": <us>}]}` |
| `max_query_range` | hours a single query may span; longer ranges are trimmed |
| `full_text_search_keys` | fields `match_all()` looks at |
| `partition_keys` | how files are partitioned - the biggest lever on query cost |
| `index_fields`, `index_all_values` | inverted index for equality lookups |
| `bloom_filter_fields` | fast "does this value exist" on high-cardinality fields |
| `defined_schema_fields` | user-defined schema: only these fields get columns |
| `flatten_level` | how deep nested JSON is flattened |
| `store_original_data`, `index_original_data` | keep the raw record alongside the parsed one |
| `distinct_value_fields`, `enable_distinct_fields` | precomputed distinct values for `_values` |
| `enable_log_patterns_extraction` | pattern extraction on this stream |
| `cross_links` | UI links out of a record: `{"name", "url": "https://x/{field}", "fields": [...]}` |

Settings change how data is stored from now on; they do not rewrite what is already there.
Shortening `data_retention` deletes data on the next cycle - confirm before sending it.

## Creating, deleting, trimming

```bash
oo post streams/my_stream -d '{"fields": [], "settings": {}}' --type logs
oo put streams/k8s_logs/delete_fields -d '{"fields": ["debug_blob"]}'
oo delete streams/my_stream --type logs --delete_all=false
```

`delete_all=true` removes the stream's alerts and dashboards with it. Both deletes are
permanent and neither asks twice - confirm with the user first.

## Ingestion

| Endpoint | Format |
|----------|--------|
| `POST /api/{org}/{stream}/_json` | a JSON array of records |
| `POST /api/{org}/{stream}/_multi` | newline-delimited JSON, one record per line |
| `POST /api/{org}/_bulk` | Elasticsearch bulk NDJSON (action line, then document) |
| `POST /api/{org}/loki/api/v1/push` | Loki push, JSON or snappy protobuf |
| `POST /api/{org}/v1/traces` | OTLP traces, protobuf or JSON |
| `POST /api/{org}/prometheus/api/v1/write` | Prometheus remote write |
| `POST /api/{org}/ingest/metrics/_json` | JSON metrics |

```bash
oo api POST /api/default/scratch_logs/_json -d '[{"level":"info","message":"hello"}]'
echo '{"level":"info","message":"hello"}' | oo api POST /api/default/scratch_logs/_multi -d @-
```

Records without `_timestamp` are stamped on arrival; otherwise supply microseconds. A stream
is created by its first write, so a typo in the name quietly creates a new stream rather than
failing. Ingest into a scratch stream, never into one that alerts or dashboards read.

## Enrichment tables

Lookup tables that VRL functions can join against - `name,value` CSV uploaded once and
referenced from a pipeline.

```bash
oo api POST /api/default/enrichment_tables/customers -f customers.csv
oo api POST /api/default/enrichment_tables/customers/url --append true -d '{"url":"https://example.com/customers.csv"}'
```

The URL form fetches in the background, so a success response only means the fetch started.

## Traces

Trace streams are searchable like any other, plus a few endpoints of their own:

```bash
oo get <stream>/traces/latest --from 0 --size 20 --start_time <us> --end_time <us>
oo get <stream>/traces/<trace_id>/dag --start_time <us> --end_time <us>
oo api GET /api/default/traces/service_graph/topology/current   # enterprise
```

`traces/latest` returns trace summaries - id, span count, services, duration - and
`.../dag` returns the spans as nodes and parent-child edges, which is the shape you want when
explaining where a request spent its time.
