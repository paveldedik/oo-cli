# Pipelines, functions and actions

## Functions (VRL)

A function is a snippet of [VRL](https://vector.dev/docs/reference/vrl/) that rewrites a
record: parse a field, drop noise, add a label.

```bash
oo get functions
oo get functions/<name>            # which pipelines depend on it - check before editing
oo post functions -d '{"name":"drop_health","function":"if .path == \"/healthz\" { abort }\n."}'
oo put functions/<name> -f function.json
oo delete functions/<name> --force=false
```

Test before you save - the endpoint runs the code against sample events and returns the
transformed output or the syntax error:

```bash
oo post functions/test -d '{"function":". |= parse_json!(.body)\n.","events":[{"body":"{\"a\":1}"}]}'
```

The VRL program's last expression is the record it emits; `abort` drops it. `transType` is
0 for VRL (1 is JavaScript, where the build supports it). Deleting a function used by a
pipeline needs `--force=true` and breaks that pipeline.

## Pipelines

A pipeline is a graph: nodes do things, edges connect them. Two kinds, decided by `source`:

- **realtime** - `{"source_type": "realtime"}`, runs on every record as it arrives
- **scheduled** - runs a query on a schedule and writes the result somewhere (a derived
  stream), with its own `query_condition` and `trigger_condition`

```bash
oo get pipelines
oo get pipelines/<pipeline_id>
oo get pipelines/streams                 # which streams have pipelines
oo put pipelines/<pipeline_id>/enable --value=false
oo delete pipelines/<pipeline_id>
```

### Nodes and edges

Every node has `id` (a UUID), `position` (`{x, y}`, only for the UI), `io_type` and `data`.
`io_type` is `input` for the source stream, `output` for the destination stream, `default`
for everything in between.

| `data.node_type` | Fields |
|------------------|--------|
| `stream` | `org_id`, `stream_name`, `stream_type` |
| `function` | `name`, `after_flatten` |
| `condition` | `version: 2`, `conditions` (a group, see below) |
| `query` | `org_id`, `stream_type`, `query_condition`, `trigger_condition` |
| `remote_stream` | `org_id`, `destination_name` (a pipeline destination) |

Edges are `{"id": "e<source>-<target>", "source": "<node id>", "target": "<node id>"}`.

```json
{
  "name": "drop_health_checks",
  "source": {"source_type": "realtime"},
  "nodes": [
    {"id": "input-1", "io_type": "input", "position": {"x": 100, "y": 100},
     "data": {"node_type": "stream", "org_id": "default", "stream_name": "app_logs", "stream_type": "logs"}},
    {"id": "func-1", "io_type": "default", "position": {"x": 100, "y": 200},
     "data": {"node_type": "function", "name": "drop_health", "after_flatten": true}},
    {"id": "output-1", "io_type": "output", "position": {"x": 100, "y": 300},
     "data": {"node_type": "stream", "org_id": "default", "stream_name": "app_logs_clean", "stream_type": "logs"}}
  ],
  "edges": [
    {"id": "einput-1-func-1", "source": "input-1", "target": "func-1"},
    {"id": "efunc-1-output-1", "source": "func-1", "target": "output-1"}
  ]
}
```

Updating is `PUT /api/{org}/pipelines` - the whole object, including `pipeline_id` and
`version` from the one you read, not a path with an id in it.

### Conditions (version 2)

A condition node holds a flat array where each item carries the boolean connector that comes
**before** it. The first item's `logicalOperator` is ignored but must be present. `AND` binds
tighter than `OR`; nest groups for explicit parentheses.

```json
{"node_type": "condition", "version": 2,
 "conditions": {"filterType": "group", "logicalOperator": "AND", "conditions": [
   {"filterType": "condition", "column": "status", "operator": "=", "value": "error", "logicalOperator": "AND"},
   {"filterType": "group", "logicalOperator": "AND", "conditions": [
     {"filterType": "condition", "column": "level", "operator": ">", "value": "5", "logicalOperator": "OR"},
     {"filterType": "condition", "column": "source", "operator": "=", "value": "nginx", "logicalOperator": "OR"}]}]}}
```

That is `status = "error" AND (level > 5 OR source = "nginx")`. Operators: `=`, `!=`, `>`,
`>=`, `<`, `<=`, `contains`, `not_contains`.

### History and backfill

```bash
oo get pipelines/history --pipeline_id <id> --start_time <us> --end_time <us> --size 100
oo get pipelines/<id>/backfill/<job_id>
oo post pipelines/<id>/backfill -f backfill.json
```

History shows each scheduled run, its status and its error - the place to look when a derived
stream stops filling. Backfill re-runs a scheduled pipeline over a past window; it costs a
full search per interval, so pick the window deliberately.

## Actions

Uploaded code packages that an alert can run (enterprise).

```bash
oo get actions
oo get actions/<action_id>
oo --raw api GET /api/default/actions/download/<ksuid> > action.zip
```
