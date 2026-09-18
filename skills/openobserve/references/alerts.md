# Alerts, destinations and templates

Three objects, in the order you need them:

1. a **template** formats the message,
2. a **destination** says where it goes and which template it uses,
3. an **alert** says what to watch and names its destinations.

Alerts live in folders and use the v2 API, so `oo get alerts` is
`GET /api/v2/{org}/alerts`. Destinations and templates are v1.

## Listing

```bash
oo get alerts                                  # every alert in the org
oo get alerts --folder default --enabled true
oo get alerts --alert_name_substring celery --alert_type scheduled
oo get alerts --stream_type logs --stream_name k8s_logs
oo get alerts --page_size 50 --page_idx 1
```

Filters: `folder` (a folder **id**), `stream_type`, `stream_name` (only with
`stream_type`), `alert_name_substring` (case-insensitive), `owner`, `enabled`,
`alert_type` (`all`, `scheduled`, `realtime`, `anomaly_detection`), `page_size`, `page_idx`.

Each item carries `alert_id`, `name`, `enabled`, `folder_id`, `folder_name`,
`is_real_time`, `last_triggered_at` and `last_satisfied_at`.

```bash
oo get alerts | jq -r '.list[] | select(.enabled) | "\(.folder_name)/\(.name)"'
```

## One alert

```bash
oo get alerts/<alert_id>                       # add --folder <id> for a non-default folder
oo post alerts/<alert_id>/export                # the same thing, shaped for re-import
oo patch alerts/<alert_id>/enable --value=false
oo patch alerts/<alert_id>/trigger              # fire it now, to test the destination
oo post alerts/<alert_id>/clone -d '{"name": "copy_of_x", "folder_id": "<id>"}'
oo patch alerts/move -d '{"alert_ids": ["<id>"], "dst_folder_id": "<id>"}'
oo delete alerts/<alert_id>                     # permanent
```

## The alert object

Names must be snake_case: no spaces and none of `: # ? & % /` or quotes. `destinations` is
required and every name in it must already exist.

```json
{
  "name": "api_error_rate",
  "stream_type": "logs",
  "stream_name": "k8s_logs",
  "is_real_time": false,
  "enabled": true,
  "description": "5xx from the API gateway",
  "destinations": ["slack_alerts"],
  "query_condition": {
    "type": "sql",
    "sql": "select count(*) as n from k8s_logs where status >= 500"
  },
  "trigger_condition": {
    "period": 10, "frequency": 600, "operator": ">=", "threshold": 5, "silence": 30
  },
  "context_attributes": {"team": "platform"},
  "row_template": "{alert_name} fired: {n}"
}
```

### `trigger_condition` - when it runs and what counts as firing

| Field | Unit | Meaning |
|-------|------|---------|
| `period` | minutes | how far back each evaluation looks |
| `frequency` | seconds | how often it evaluates (`frequency_type: "minutes"`) |
| `frequency_type` | - | `minutes` or `cron` |
| `cron` | - | schedule when `frequency_type` is `cron` |
| `timezone` | - | timezone for the cron expression |
| `operator` | - | `=`, `!=`, `>`, `>=`, `<`, `<=`, `contains`, `not_contains` |
| `threshold` | - | compared against the row count or the aggregate |
| `silence` | minutes | mute after firing, so one incident is one notification |
| `align_time` | - | snap evaluations to the clock |
| `tolerance_in_secs` | seconds | slack for late-arriving data |

`period` shorter than the data's ingestion delay is the usual reason an alert never fires.

### `query_condition` - what it asks

`type` is one of three, and the other fields follow from it:

- **`custom`** - `conditions` (a condition group), optional `aggregation`, `vrl_function`,
  `multi_time_range`. The UI builds this one.
- **`sql`** - `sql` plus optional `vrl_function`. The query must return rows only when
  something is wrong, or return a number that `trigger_condition` compares.
- **`promql`** - `promql` plus `promql_condition` (`{"column", "operator", "value"}`), for
  alerts on metrics.

`aggregation` narrows a custom alert: `function` is one of `avg`, `min`, `max`, `sum`,
`count`, `median`, `p50`, `p75`, `p90`, `p95`, `p99`, with `group_by` and a `having` clause
shaped `{"column", "operator", "value", "ignore_case"}`.

`POST /api/v2/{org}/alerts/generate_sql` turns a custom condition into the SQL it would run -
useful for checking an alert before saving it.

The `conditions` group is the same nested format pipelines use (see `pipelines.md`):
`{"filterType": "group", "logicalOperator": "AND", "conditions": [...]}` with leaves
`{"filterType": "condition", "column", "operator", "value", "logicalOperator"}`. When in
doubt, build one alert in the UI, `oo get alerts/<id>`, and copy the shape.

### Editing an existing alert

```bash
oo get alerts/<id> > alert.json
jq '.trigger_condition.threshold = 10' alert.json > patched.json
oo put alerts/<id> -f patched.json
```

`PUT` replaces the object, so always start from the current one.

## Destinations

```bash
oo get alerts/destinations
oo get alerts/destinations --module pipeline     # pipeline destinations instead
oo get alerts/destinations/<name>
oo post alerts/destinations -d '{"name":"slack_alerts","type":"http","url":"https://hooks.example.com/x","method":"post","template":"Default"}'
oo post alerts/destinations -d '{"name":"oncall_mail","type":"email","emails":["oncall@example.com"],"template":"Default"}'
oo delete alerts/destinations/<name>
```

`template` is **required** for an alert destination - without it the destination is created
as a pipeline destination and no alert can use it. `type` is `http`, `email` or `sns`
(`sns_topic_arn` + `aws_region`). `headers` adds HTTP headers, `skip_tls_verify` disables
certificate checks. A destination in use cannot be deleted.

## Templates

```bash
oo get alerts/templates
oo get alerts/templates/system/prebuilt      # read-only, Slack/Teams/PagerDuty/...
oo get alerts/templates/<name>
oo post alerts/templates -d '{"name":"short","type":"http","body":"{\"text\":\"{alert_name} fired\"}"}'
```

`body` is the message with `{variable}` placeholders; `title` is used for email. Variables
come from the alert (`alert_name`, `stream_name`, `org_name`, `alert_start_time`, ...),
its `context_attributes`, and the matching rows via `row_template`. Templates named
`system_*` are prebuilt and read-only.

## History and incidents

```bash
oo get alerts/history --alert_id <id> --start_time <us> --end_time <us> --size 100
oo get alerts/history --sort_by timestamp --sort_order desc
```

History comes from the org's own triggers stream: when an alert ran, whether it was
satisfied, whether it was silenced, how long the evaluation took, and any error. It is the
first place to look when someone says an alert did not fire.

Incidents group notifications for alerts with `creates_incident: true`:

```bash
oo get alerts/incidents --status open --limit 20   # open, acknowledged or resolved
oo get alerts/incidents/stats
oo get alerts/incidents/<incident_id>
oo patch alerts/incidents/<incident_id>/update -d '{"status":"resolved"}'  # one field per call
```

Deduplication (`alerts/deduplication/...`) and RCA are enterprise features; on OSS they
answer "not supported".

## Folders

```bash
oo get folders/alerts                        # folder_type is dashboards, alerts or reports
oo get folders/alerts/name/<folder_name>
oo post folders/alerts -d '{"name":"platform","description":"team alerts"}'
oo delete folders/alerts/<folder_id>
```

`--folder` everywhere takes the **folderId**, not the name. The default folder's id is
literally `default`.
