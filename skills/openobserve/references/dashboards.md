# Dashboards, panels and reports

## Listing and reading

```bash
oo get dashboards                          # the default folder
oo get dashboards --folder <folder_id>
oo get dashboards --title latency          # case-insensitive substring
oo get dashboards/<dashboard_id> --folder <folder_id>
```

With no `--folder` you get the default folder only; with a filter such as `--title` and no
folder you get matches from every folder. The list comes back as `{"dashboards": [...]}` with `dashboard_id`, `title`, `folder_id`,
`folder_name`, `owner`, `version` and - importantly - `hash`.

```bash
oo get dashboards | jq -r '.dashboards[] | "\(.dashboard_id)  \(.folder_name)/\(.title)"'
```

Exporting is just reading: `oo get dashboards/<id> --folder <id> > dashboard.json`. That
file is what you commit, diff or move to another instance.

## Updating: the `hash` matters

```bash
oo get dashboards/<id> --folder default > d.json
jq '.title = "API latency"' d.json > patched.json
oo put dashboards/<id> --folder default --hash "$(jq -r .hash d.json)" -f patched.json
```

`folder` is required on `PUT`, and `hash` is the optimistic-locking token from the object you
read. Without it a concurrent edit in the UI is overwritten silently. Every write returns a
new hash; use that one for the next call.

## Panels without rewriting the dashboard

```bash
oo post dashboards/<id>/panels --folder default --hash <hash> -f panel.json
oo put dashboards/<id>/panels/<panel_id> --folder default --hash <hash> -f panel.json
oo delete dashboards/<id>/panels/<panel_id> --folder default --hash <hash> --tabId <tab>
```

Adding a panel computes the layout for you and returns the new hash, so several panels can be
added one after another. The body is `{"panel": {...}, "tabId": "..."}`.

### The panel object

A dashboard is `{title, description, tabs: [{tabId, name, panels: [...]}], variables, version}`.
A panel needs `id`, `type`, `title`, `description`, `config` and `queries`.

Layout is a **192-column grid**: `layout` is `{x, y, w, h, i}` where `x` is the column
(0-191), `y` the row, `w` the width (full = 192, half = 96, a third = 64), `h` the height and
`i` the panel's own id. Let `POST .../panels` place it unless you need an exact position.

Every query needs `fields` filled in **even when `customQuery` is true**, because the axes
tell the renderer which returned column is which:

- `x` - the dimension, usually the time bucket
- `y` - the metric column or columns
- `z` - only heatmaps (colour), stacked charts (breakdown) and geo maps (value); `[]` for
  line, area, bar and pie
- `filter` must be an **object**, not an array: `{"type":"list","values":[],"logicalOperator":"AND","filterType":"list"}`

Column values are the SQL aliases. For
`select histogram(_timestamp) as ts, count(*) as cnt from k8s_logs`:

```json
{
  "id": "panel_errors",
  "type": "line",
  "title": "Errors per minute",
  "description": "",
  "queryType": "sql",
  "queries": [{
    "customQuery": true,
    "query": "select histogram(_timestamp) as ts, count(*) as cnt from k8s_logs where level = 'error' group by ts order by ts",
    "fields": {
      "stream": "k8s_logs",
      "stream_type": "logs",
      "x": [{"label": "ts", "alias": "ts", "column": "ts", "aggregationFunction": null}],
      "y": [{"label": "cnt", "alias": "cnt", "column": "cnt", "aggregationFunction": null}],
      "z": [],
      "filter": {"type": "list", "values": [], "logicalOperator": "AND", "filterType": "list"}
    },
    "config": {"promql_legend": ""}
  }],
  "config": {"show_legends": true}
}
```

Panel JSON is long and fussy. Building one in the UI and reading it back beats writing it
from scratch; copy a working panel and change the query and the aliases.

## Annotations

```bash
oo get dashboards/<id>/annotations --start_time <us> --end_time <us> --panels <panel_id>
oo post dashboards/<id>/annotations -d '{"timed_annotations":[{"title":"deploy 1.4.2","start_time":1789700000000000,"panels":["panel_errors"],"tags":["deploy"]}]}'
oo put dashboards/<id>/annotations/<annotation_id> -f annotation.json
oo delete dashboards/<id>/annotations -d '{"annotation_ids":["..."]}'
```

`end_time` turns a marker into a range. Times are microseconds.

## Folders and moving

```bash
oo get folders/dashboards
oo post folders/dashboards -d '{"name":"platform","description":"team dashboards"}'
oo patch dashboards/move -d '{"dashboard_ids":["<id>"],"dst_folder_id":"<folder_id>"}'
oo put folders/dashboards/<dashboard_id> -d '{"from":"<folder_id>","to":"<folder_id>"}'
```

## Scheduled reports

A report renders one or more dashboard tabs and emails them on a schedule. `oo get reports`
is the v2 endpoint, so reports are addressed by `report_id`.

```bash
oo get reports
oo get reports --folder <folder_id> --dashboard_id <id>
oo get reports/<report_id>
oo patch reports/<report_id>/enable --value=true
oo put reports/<report_id>/trigger                 # send it now
oo delete reports/<report_id>
```

Creating one:

```json
{
  "name": "weekly_latency",
  "title": "Weekly latency",
  "orgId": "default",
  "enabled": true,
  "dashboards": [{
    "dashboard": "<dashboard_id>",
    "folder": "<folder_id>",
    "tabs": ["<tabId>"],
    "report_type": "pdf",
    "timerange": {"type": "relative", "period": "7d", "from": 0, "to": 0}
  }],
  "destinations": [{"email": "team@example.com"}],
  "frequency": {"type": "weeks", "interval": 1},
  "start": 1789700000000000,
  "timezone": "Europe/Prague",
  "message": "Latency for the past week"
}
```

`report_type` is `pdf`, `png` or `csv`; `frequency.type` is `once`, `hours`, `days`,
`weeks`, `months` or `cron` (with `cron` holding the expression); `start` is in
microseconds. `variables` fills dashboard variables, `imagePreview` embeds a PNG next to a
PDF. Reports render in a headless browser on the server, so a report that produces nothing
usually means the dashboard needs variables the report did not supply.
