# Metrics and PromQL

OpenObserve serves the Prometheus HTTP API under `/api/{org}/prometheus/api/v1/...`, so
anything you know from Prometheus works, and so does any tool that speaks it. These paths do
not fit the `oo <verb> <resource>` rule; use `oo api`.

Times here follow Prometheus, **not** the rest of OpenObserve: RFC 3339 or unix **seconds**,
not microseconds.

## Instant query

```bash
oo api GET /api/default/prometheus/api/v1/query --query "up"
oo api GET /api/default/prometheus/api/v1/query \
  --query 'sum by (namespace) (rate(http_requests_total[5m]))' --time 1789700000
```

`time` defaults to now. The result is the Prometheus envelope:
`{"status": "success", "data": {"resultType": "vector", "result": [...]}}`.

```bash
oo api GET /api/default/prometheus/api/v1/query --query "up" \
  | jq -r '.data.result[] | "\(.metric.instance) \(.value[1])"'
```

## Range query

```bash
oo api GET /api/default/prometheus/api/v1/query_range \
  --query 'sum(rate(http_requests_total[5m]))' \
  --start 1789700000 --end 1789703600 --step 60
```

`start`, `end` and `query` are required; `step` is a duration (`60`, `1m`) and decides how
many points come back. Points = range / step: keep that in the low thousands. A month at a
30-second step is hundreds of thousands of points per series and is the classic way to make
an instance run out of memory - widen the step, or aggregate into a recording rule instead.

## Discovery

```bash
oo api GET /api/default/prometheus/api/v1/labels --match[] 'up' --start ... --end ...
oo api GET /api/default/prometheus/api/v1/label/namespace/values --match[] 'up' --start ... --end ...
oo api GET /api/default/prometheus/api/v1/series --match[] 'up{job="api"}' --start ... --end ...
oo api GET /api/default/prometheus/api/v1/metadata --limit 100 --metric http_requests_total
oo api GET /api/default/prometheus/api/v1/format_query --query 'sum(  rate(x[5m]) )'
```

`labels` and `series` need `match[]`, `start` and `end`. `metadata` gives a metric's type and
help text, which is how you tell a counter from a gauge before writing `rate()`.

Metrics are also streams, so `oo get streams --type metrics` lists them and
`oo get streams/<metric>/schema --type metrics` shows the label columns. And SQL works:
`oo search --type metrics --sql "select * from up limit 5" --from -5m`.

## Ingestion

| Endpoint | Format |
|----------|--------|
| `POST /api/{org}/prometheus/api/v1/write` | Prometheus remote write (snappy protobuf) |
| `POST /api/{org}/ingest/metrics/_json` | JSON array, one object per sample |

In the JSON form `__name__` is the metric (and the stream) name, `__type__` is `counter`,
`gauge`, `histogram` or `summary`, `value` is the sample, and every other key is a label:

```bash
oo api POST /api/default/ingest/metrics/_json \
  -d '[{"__name__":"batch_done","__type__":"counter","_timestamp":1789700000,"job":"nightly","value":1.2}]'
```

Ingestion writes real data into a real instance. Do it to a scratch stream, never to one an
alert or dashboard reads.
