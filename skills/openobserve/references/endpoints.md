# Every endpoint, as the command that reaches it

Generated from an OpenObserve instance's own `/api-doc/openapi.json` (v0.91). Your instance
is the authority - `oo spec paths <needle>` lists what it actually serves, and enterprise
builds carry endpoints an OSS build answers "not supported" for.

Notation: `<name>` is a path parameter you substitute, `{org}` comes from `OO_ORG`, and a
query parameter marked `*` is required. Anything shown as `oo api` does not fit the
`oo <verb> <resource>` rule - usually because the path is not under the organization, or
starts with an underscore.

## Search

- `oo api POST /api/{org}/_search` — POST `/api/{org_id}/_search`
  Search data with SQL
  query: type, is_ui_histogram, is_multi_stream_search, validate
  body required
- `oo api POST /api/{org}/_search_history` — POST `/api/{org_id}/_search_history`
  Search query history
  body required
- `oo api POST /api/{org}/_search_partition` — POST `/api/{org_id}/_search_partition`
  Search partition data
  query: type
  body required
- `oo api POST /api/{org}/_search_stream` — POST `/api/{org_id}/_search_stream`
  Stream search results
  query: is_ui_histogram*, is_multi_stream_search*
  body required
- `oo api POST /api/{org}/_values_stream` — POST `/api/{org_id}/_values_stream`
  Get field values with HTTP/2 streaming
  body required
- `oo get <stream_name>/_around` — GET `/api/{org_id}/{stream_name}/_around`
  Search around specific log entry
  query: type, key*, size*, regions, timeout
- `oo post <stream_name>/_around` — POST `/api/{org_id}/{stream_name}/_around`
  Search around specific log record
  query: size*, regions, timeout
  body required
- `oo get <stream_name>/_values` — GET `/api/{org_id}/{stream_name}/_values`
  Get distinct field values
  query: type, fields*, filter, keyword, size*, from*, start_time*, end_time*, regions, timeout, no_count

## Search Jobs

- `oo get search_jobs` — GET `/api/{org_id}/search_jobs`
  List search jobs
- `oo post search_jobs` — POST `/api/{org_id}/search_jobs`
  Submit search job
  body required
- `oo delete search_jobs/<job_id>` — DELETE `/api/{org_id}/search_jobs/{job_id}`
  Delete search job
- `oo get search_jobs/<job_id>` — GET `/api/{org_id}/search_jobs/{job_id}`
  Get search job status
- `oo post search_jobs/<job_id>/cancel` — POST `/api/{org_id}/search_jobs/{job_id}/cancel`
  Cancel search job
- `oo get search_jobs/<job_id>/result` — GET `/api/{org_id}/search_jobs/{job_id}/result`
  Get search job results
  query: from, size
- `oo post search_jobs/<job_id>/retry` — POST `/api/{org_id}/search_jobs/{job_id}/retry`
  Retry search job

## Streams

- `oo get streams` — GET `/api/{org_id}/streams`
  List organization streams
  query: type, keyword, offset, limit, sort
- `oo delete streams/<stream_name>` — DELETE `/api/{org_id}/streams/{stream_name}`
  Delete stream
  query: type, delete_all*
- `oo post streams/<stream_name>` — POST `/api/{org_id}/streams/{stream_name}`
  Create new stream
  query: type
  body required
- `oo put streams/<stream_name>/delete_fields` — PUT `/api/{org_id}/streams/{stream_name}/delete_fields`
  Delete stream fields
  query: type
  body required
- `oo get streams/<stream_name>/schema` — GET `/api/{org_id}/streams/{stream_name}/schema`
  Get stream schema
  query: type, keyword, offset, limit
- `oo put streams/<stream_name>/settings` — PUT `/api/{org_id}/streams/{stream_name}/settings`
  Update stream settings
  query: type
  body required

## Ingestion — logs

- `oo api POST /api/{org}/_bulk` — POST `/api/{org_id}/_bulk`
  Bulk ingest logs (Elasticsearch compatible)
  body required
- `oo post loki/api/v1/push` — POST `/api/{org_id}/loki/api/v1/push`
  Ingest logs via Loki API
  body required
- `oo post <stream_name>/_json` — POST `/api/{org_id}/{stream_name}/_json`
  Ingest logs via JSON array
  body required
- `oo post <stream_name>/_multi` — POST `/api/{org_id}/{stream_name}/_multi`
  Ingest logs via multi-line JSON
  body required

## Metrics and PromQL

- `oo post ingest/metrics/_json` — POST `/api/{org_id}/ingest/metrics/_json`
  Ingest metrics via JSON
  body required
- `oo get prometheus/api/v1/format_query` — GET `/api/{org_id}/prometheus/api/v1/format_query`
  Format Prometheus query
  query: query*
- `oo get prometheus/api/v1/label/<label_name>/values` — GET `/api/{org_id}/prometheus/api/v1/label/{label_name}/values`
  Get label values
  query: match[]*, start, end
- `oo get prometheus/api/v1/labels` — GET `/api/{org_id}/prometheus/api/v1/labels`
  Get metric label names
  query: match[]*, start, end
- `oo get prometheus/api/v1/metadata` — GET `/api/{org_id}/prometheus/api/v1/metadata`
  Get metric metadata
  query: limit*, metric
- `oo get prometheus/api/v1/query` — GET `/api/{org_id}/prometheus/api/v1/query`
  Execute Prometheus instant query
  query: query*, time, timeout
- `oo get prometheus/api/v1/query_range` — GET `/api/{org_id}/prometheus/api/v1/query_range`
  Execute Prometheus range query
  query: query*, start*, end*, step, timeout
- `oo get prometheus/api/v1/series` — GET `/api/{org_id}/prometheus/api/v1/series`
  Find metric series
  query: match[]*, start, end
- `oo post prometheus/api/v1/write` — POST `/api/{org_id}/prometheus/api/v1/write`
  Ingest Prometheus metrics
  body required

## Traces

- `oo get traces/service_graph/topology/current` — GET `/api/{org_id}/traces/service_graph/topology/current`
  Get current service graph topology
  query: stream_name
- `oo post v1/traces` — POST `/api/{org_id}/v1/traces`
  Ingest trace data
  body required
- `oo get <stream_name>/traces/latest` — GET `/api/{org_id}/{stream_name}/traces/latest`
  Get recent trace data
  query: filter, from*, size*, start_time*, end_time*, timeout, sort_by, sort_order
- `oo get <stream_name>/traces/session` — GET `/api/{org_id}/{stream_name}/traces/session`
  Get recent session data
  query: filter, from*, size*, start_time*, end_time*, timeout
- `oo get <stream_name>/traces/user` — GET `/api/{org_id}/{stream_name}/traces/user`
  Get recent user data
  query: filter, from*, size*, start_time*, end_time*, timeout
- `oo get <stream_name>/traces/<trace_id>/dag` — GET `/api/{org_id}/{stream_name}/traces/{trace_id}/dag`
  Get trace DAG structure
  query: start_time*, end_time*, timeout

## RUM

- `oo api POST /rum/v1/{org}/logs` — POST `/rum/v1/{org_id}/logs`
  Ingest RUM log events
  body required
- `oo api POST /rum/v1/{org}/replay` — POST `/rum/v1/{org_id}/replay`
  Ingest session replay data
  body required
- `oo api POST /rum/v1/{org}/rum` — POST `/rum/v1/{org_id}/rum`
  Ingest RUM data events
  body required

## Alerts, destinations, templates

- `oo get alerts` — GET `/api/v2/{org_id}/alerts`
  List organization alerts
  query: folder, stream_type, stream_name, alert_name_substring, owner, enabled, page_size, page_idx, alert_type
- `oo post alerts` — POST `/api/v2/{org_id}/alerts`
  Create new alert
  query: folder
  body required
- `oo post alerts/bulk/enable` — POST `/api/v2/{org_id}/alerts/bulk/enable`
  Enable or disable alert in bulk
  query: value*, folder
  body required
- `oo post alerts/generate_sql` — POST `/api/v2/{org_id}/alerts/generate_sql`
  Generate SQL from alert query parameters
  body required
- `oo patch alerts/move` — PATCH `/api/v2/{org_id}/alerts/move`
  Move alerts between folders
  query: folder
  body required
- `oo delete alerts/<alert_id>` — DELETE `/api/v2/{org_id}/alerts/{alert_id}`
  Delete alert
  query: folder
- `oo get alerts/<alert_id>` — GET `/api/v2/{org_id}/alerts/{alert_id}`
  Get alert details
  query: folder
- `oo put alerts/<alert_id>` — PUT `/api/v2/{org_id}/alerts/{alert_id}`
  Update alert configuration
  query: folder
  body required
- `oo post alerts/<alert_id>/clone` — POST `/api/v2/{org_id}/alerts/{alert_id}/clone`
  Clone an alert or anomaly detection config
  query: folder
  body required
- `oo patch alerts/<alert_id>/enable` — PATCH `/api/v2/{org_id}/alerts/{alert_id}/enable`
  Enable or disable alert
  query: value*, folder
- `oo post alerts/<alert_id>/export` — POST `/api/v2/{org_id}/alerts/{alert_id}/export`
  Export alert configuration
  query: folder
- `oo patch alerts/<alert_id>/retrain` — PATCH `/api/v2/{org_id}/alerts/{alert_id}/retrain`
  Trigger retraining for an anomaly detection alert
- `oo patch alerts/<alert_id>/trigger` — PATCH `/api/v2/{org_id}/alerts/{alert_id}/trigger`
  Manually trigger alert
  query: folder
- `oo get alerts/dedup/summary` — GET `/api/{org_id}/alerts/dedup/summary`
  Get deduplication summary statistics for an organization
- `oo delete alerts/deduplication/config` — DELETE `/api/{org_id}/alerts/deduplication/config`
  Delete deduplication configuration for an organization (OSS - Not Supported)
- `oo get alerts/deduplication/config` — GET `/api/{org_id}/alerts/deduplication/config`
  Get deduplication configuration for an organization (OSS - Not Supported)
- `oo post alerts/deduplication/config` — POST `/api/{org_id}/alerts/deduplication/config`
  Set deduplication configuration for an organization (OSS - Not Supported)
  body required
- `oo get alerts/deduplication/semantic-groups` — GET `/api/{org_id}/alerts/deduplication/semantic-groups`
  Get semantic field groups (OSS - Not Supported)
- `oo put alerts/deduplication/semantic-groups` — PUT `/api/{org_id}/alerts/deduplication/semantic-groups`
  Save semantic groups (OSS - Not Supported)
  body required
- `oo post alerts/deduplication/semantic-groups/preview-diff` — POST `/api/{org_id}/alerts/deduplication/semantic-groups/preview-diff`
  Preview diff (OSS - Not Supported)
  body required
- `oo get alerts/destinations` — GET `/api/{org_id}/alerts/destinations`
  List alert destinations
  query: module
- `oo post alerts/destinations` — POST `/api/{org_id}/alerts/destinations`
  Create alert or pipeline destination
  query: module
  body required
- `oo delete alerts/destinations/<destination_name>` — DELETE `/api/{org_id}/alerts/destinations/{destination_name}`
  Delete alert destination
- `oo get alerts/destinations/<destination_name>` — GET `/api/{org_id}/alerts/destinations/{destination_name}`
  Get alert destination
- `oo put alerts/destinations/<destination_name>` — PUT `/api/{org_id}/alerts/destinations/{destination_name}`
  Update alert or pipeline destination
  query: module
  body required
- `oo get alerts/history` — GET `/api/{org_id}/alerts/history`
  Get alert execution history
  query: alert_id, start_time, end_time, from, size, sort_by, sort_order

## Templates

- `oo get alerts/templates` — GET `/api/{org_id}/alerts/templates`
  List alert templates
- `oo post alerts/templates` — POST `/api/{org_id}/alerts/templates`
  Create alert template
  body required
- `oo get alerts/templates/system/prebuilt` — GET `/api/{org_id}/alerts/templates/system/prebuilt`
  Get system prebuilt templates
- `oo delete alerts/templates/<template_name>` — DELETE `/api/{org_id}/alerts/templates/{template_name}`
  Delete alert template
- `oo get alerts/templates/<template_name>` — GET `/api/{org_id}/alerts/templates/{template_name}`
  Get alert template
- `oo put alerts/templates/<template_name>` — PUT `/api/{org_id}/alerts/templates/{template_name}`
  Update alert template
  body required

## Incidents

- `oo get alerts/incidents` — GET `/api/v2/{org_id}/alerts/incidents`
  List alert incidents
  query: status, limit, offset
- `oo get alerts/incidents/stats` — GET `/api/v2/{org_id}/alerts/incidents/stats`
  Get incident statistics
- `oo get alerts/incidents/<incident_id>` — GET `/api/v2/{org_id}/alerts/incidents/{incident_id}`
  Get incident details
- `oo post alerts/incidents/<incident_id>/rca` — POST `/api/v2/{org_id}/alerts/incidents/{incident_id}/rca`
  Trigger RCA analysis for an incident
- `oo patch alerts/incidents/<incident_id>/update` — PATCH `/api/v2/{org_id}/alerts/incidents/{incident_id}/update`
  Update incident fields
  body required

## Dashboards

- `oo get dashboards` — GET `/api/{org_id}/dashboards`
  List organization dashboards
  query: folder, title, pageSize
- `oo post dashboards` — POST `/api/{org_id}/dashboards`
  Create new dashboard
  query: folder
  body required
- `oo patch dashboards/move` — PATCH `/api/{org_id}/dashboards/move`
  Move multiple dashboards
  body required
- `oo delete dashboards/<dashboard_id>` — DELETE `/api/{org_id}/dashboards/{dashboard_id}`
  Delete dashboard
  query: folder
- `oo get dashboards/<dashboard_id>` — GET `/api/{org_id}/dashboards/{dashboard_id}`
  Get dashboard details
  query: folder
- `oo put dashboards/<dashboard_id>` — PUT `/api/{org_id}/dashboards/{dashboard_id}`
  Update existing dashboard
  query: folder*, hash
  body required
- `oo delete dashboards/<dashboard_id>/annotations` — DELETE `/api/{org_id}/dashboards/{dashboard_id}/annotations`
  Delete timed annotations from dashboard
  body required
- `oo get dashboards/<dashboard_id>/annotations` — GET `/api/{org_id}/dashboards/{dashboard_id}/annotations`
  Get timed annotations for dashboard
  query: panels, start_time*, end_time*
- `oo post dashboards/<dashboard_id>/annotations` — POST `/api/{org_id}/dashboards/{dashboard_id}/annotations`
  Create timed annotations for dashboard
  body required
- `oo delete dashboards/<dashboard_id>/annotations/panels/<timed_annotation_id>` — DELETE `/api/{org_id}/dashboards/{dashboard_id}/annotations/panels/{timed_annotation_id}`
  Remove timed annotation from panel
  body required
- `oo put dashboards/<dashboard_id>/annotations/<timed_annotation_id>` — PUT `/api/{org_id}/dashboards/{dashboard_id}/annotations/{timed_annotation_id}`
  Update timed annotation
  body required
- `oo post dashboards/<dashboard_id>/panels` — POST `/api/{org_id}/dashboards/{dashboard_id}/panels`
  Add a panel to a dashboard
  query: folder, hash*
  body required
- `oo delete dashboards/<dashboard_id>/panels/<panel_id>` — DELETE `/api/{org_id}/dashboards/{dashboard_id}/panels/{panel_id}`
  Delete a single panel from a dashboard
  query: folder, hash*, tabId
- `oo put dashboards/<dashboard_id>/panels/<panel_id>` — PUT `/api/{org_id}/dashboards/{dashboard_id}/panels/{panel_id}`
  Update a single panel in a dashboard
  query: folder, hash*
  body required
- `oo put folders/dashboards/<dashboard_id>` — PUT `/api/{org_id}/folders/dashboards/{dashboard_id}`
  Move dashboard to folder
  body required

## Folders

- `oo get folders/<folder_type>` — GET `/api/v2/{org_id}/folders/{folder_type}`
  List organization folders
- `oo post folders/<folder_type>` — POST `/api/v2/{org_id}/folders/{folder_type}`
  Create new folder
  body required
- `oo get folders/<folder_type>/name/<folder_name>` — GET `/api/v2/{org_id}/folders/{folder_type}/name/{folder_name}`
  Get folder by name
- `oo delete folders/<folder_type>/<folder_id>` — DELETE `/api/v2/{org_id}/folders/{folder_type}/{folder_id}`
  Delete folder
- `oo get folders/<folder_type>/<folder_id>` — GET `/api/v2/{org_id}/folders/{folder_type}/{folder_id}`
  Get folder details
- `oo put folders/<folder_type>/<folder_id>` — PUT `/api/v2/{org_id}/folders/{folder_type}/{folder_id}`
  Update folder details
  body required
- `oo get folders` — GET `/api/{org_id}/folders`
  List all folders (deprecated)
- `oo post folders` — POST `/api/{org_id}/folders`
  Create a new folder (deprecated)
  body required
- `oo get folders/name/<folder_name>` — GET `/api/{org_id}/folders/name/{folder_name}`
  Get folder by name (deprecated)
- `oo delete folders/<folder_id>` — DELETE `/api/{org_id}/folders/{folder_id}`
  Delete a folder (deprecated)
- `oo get folders/<folder_id>` — GET `/api/{org_id}/folders/{folder_id}`
  Get folder by ID (deprecated)
- `oo put folders/<folder_id>` — PUT `/api/{org_id}/folders/{folder_id}`
  Update an existing folder (deprecated)
  body required

## Reports

- `oo get reports` — GET `/api/v2/{org_id}/reports`
  List dashboard reports (v2)
  query: folder, dashboard_id, cache
- `oo post reports` — POST `/api/v2/{org_id}/reports`
  Create dashboard report (v2)
  query: folder
  body required
- `oo delete reports/bulk` — DELETE `/api/v2/{org_id}/reports/bulk`
  Delete multiple dashboard reports by ID (v2)
  query: folder
  body required
- `oo patch reports/move` — PATCH `/api/v2/{org_id}/reports/move`
  Move reports between folders (v2)
  query: folder
  body required
- `oo delete reports/<report_id>` — DELETE `/api/v2/{org_id}/reports/{report_id}`
  Delete dashboard report by ID (v2)
- `oo get reports/<report_id>` — GET `/api/v2/{org_id}/reports/{report_id}`
  Get dashboard report by ID (v2)
- `oo put reports/<report_id>` — PUT `/api/v2/{org_id}/reports/{report_id}`
  Update dashboard report by ID (v2)
  query: folder
  body required
- `oo patch reports/<report_id>/enable` — PATCH `/api/v2/{org_id}/reports/{report_id}/enable`
  Enable or disable a report by ID (v2)
  query: value*
- `oo put reports/<report_id>/trigger` — PUT `/api/v2/{org_id}/reports/{report_id}/trigger`
  Manually trigger a report by ID (v2)
- `oo get reports` — GET `/api/{org_id}/reports`
  List dashboard reports
- `oo post reports` — POST `/api/{org_id}/reports`
  Create dashboard report
  body required
- `oo delete reports/<name>` — DELETE `/api/{org_id}/reports/{name}`
  Delete dashboard report
- `oo get reports/<name>` — GET `/api/{org_id}/reports/{name}`
  Get dashboard report
- `oo put reports/<name>` — PUT `/api/{org_id}/reports/{name}`
  Update dashboard report
  body required
- `oo put reports/<name>/trigger` — PUT `/api/{org_id}/reports/{name}/trigger`
  Manually trigger dashboard report

- `oo put reports/<name>/enable` — PUT `/api/{org_id}/reports/{name}/enable`
  Enable or disable dashboard report
  query: value*

## Pipelines

- `oo get pipelines` — GET `/api/{org_id}/pipelines`
  List organization pipelines
- `oo post pipelines` — POST `/api/{org_id}/pipelines`
  Create new pipeline
  body required
- `oo put pipelines` — PUT `/api/{org_id}/pipelines`
  Update pipeline
  body required
- `oo get pipelines/backfill` — GET `/api/{org_id}/pipelines/backfill`
- `oo post pipelines/bulk/enable` — POST `/api/{org_id}/pipelines/bulk/enable`
  Enable or disable pipeline in bulk
  query: value*
  body required
- `oo get pipelines/history` — GET `/api/{org_id}/pipelines/history`
  Get pipeline execution history
  query: pipeline_id, start_time, end_time, from, size, sort_by, sort_order
- `oo get pipelines/streams` — GET `/api/{org_id}/pipelines/streams`
  Get streams with pipelines
- `oo delete pipelines/<pipeline_id>` — DELETE `/api/{org_id}/pipelines/{pipeline_id}`
  Delete pipeline
- `oo get pipelines/<pipeline_id>` — GET `/api/{org_id}/pipelines/{pipeline_id}`
  Get pipeline by ID
- `oo post pipelines/<pipeline_id>/backfill` — POST `/api/{org_id}/pipelines/{pipeline_id}/backfill`
  body required
- `oo delete pipelines/<pipeline_id>/backfill/<job_id>` — DELETE `/api/{org_id}/pipelines/{pipeline_id}/backfill/{job_id}`
- `oo get pipelines/<pipeline_id>/backfill/<job_id>` — GET `/api/{org_id}/pipelines/{pipeline_id}/backfill/{job_id}`
- `oo put pipelines/<pipeline_id>/backfill/<job_id>` — PUT `/api/{org_id}/pipelines/{pipeline_id}/backfill/{job_id}`
  body required
- `oo put pipelines/<pipeline_id>/backfill/<job_id>/enable` — PUT `/api/{org_id}/pipelines/{pipeline_id}/backfill/{job_id}/enable`
  query: value*
- `oo put pipelines/<pipeline_id>/enable` — PUT `/api/{org_id}/pipelines/{pipeline_id}/enable`
  Enable or disable pipeline
  query: value*

## Functions and enrichment tables

- `oo post enrichment_tables/<table_name>` — POST `/api/{org_id}/enrichment_tables/{table_name}`
  Create or update enrichment table
- `oo post enrichment_tables/<table_name>/url` — POST `/api/{org_id}/enrichment_tables/{table_name}/url`
  Create enrichment table from URL
  query: append
  body required
- `oo get functions` — GET `/api/{org_id}/functions`
  List organization functions
- `oo post functions` — POST `/api/{org_id}/functions`
  Create new function
  body required
- `oo post functions/test` — POST `/api/{org_id}/functions/test`
  Validate VRL function syntax
  body required
- `oo delete functions/<name>` — DELETE `/api/{org_id}/functions/{name}`
  Delete function
  query: force*
- `oo get functions/<name>` — GET `/api/{org_id}/functions/{name}`
  Get function pipeline dependencies
- `oo put functions/<name>` — PUT `/api/{org_id}/functions/{name}`
  Update function
  body required

## Actions

- `oo get actions` — GET `/api/{org_id}/actions`
  List automated actions
- `oo get actions/download/<ksuid>` — GET `/api/{org_id}/actions/download/{ksuid}`
  Download action package
- `oo post actions/upload` — POST `/api/{org_id}/actions/upload`
  Upload automated action package
- `oo get actions/<action_id>` — GET `/api/{org_id}/actions/{action_id}`
  Get automated action details
- `oo put actions/<action_id>` — PUT `/api/{org_id}/actions/{action_id}`
  Update automated action
  body required
- `oo delete actions/<ksuid>` — DELETE `/api/{org_id}/actions/{ksuid}`
  Delete automated action

## Saved views

- `oo get savedviews` — GET `/api/{org_id}/savedviews`
  List saved views
- `oo post savedviews` — POST `/api/{org_id}/savedviews`
  Create a new saved view
  body required
- `oo delete savedviews/<view_id>` — DELETE `/api/{org_id}/savedviews/{view_id}`
  Delete saved view
- `oo get savedviews/<view_id>` — GET `/api/{org_id}/savedviews/{view_id}`
  Get saved view
- `oo put savedviews/<view_id>` — PUT `/api/{org_id}/savedviews/{view_id}`
  Update an existing saved view
  body required

## Organizations and settings

- `oo get organizations` — GET `/api/organizations`
  Get user's organizations
- `oo post organizations` — POST `/api/organizations`
  Create new organization
  body required
- `oo post organizations/assume_service_account` — POST `/api/{org_id}/organizations/assume_service_account`
  body required
- `oo get passcode` — GET `/api/{org_id}/passcode`
  Get user's ingestion token
- `oo put passcode` — PUT `/api/{org_id}/passcode`
  Update user's ingestion token
- `oo put rename` — PUT `/api/{org_id}/rename`
  Rename organization
  body required
- `oo get rumtoken` — GET `/api/{org_id}/rumtoken`
  Get user's RUM ingestion token
- `oo post rumtoken` — POST `/api/{org_id}/rumtoken`
  Create user's RUM ingestion token
- `oo put rumtoken` — PUT `/api/{org_id}/rumtoken`
  Update user's RUM ingestion token
- `oo get settings` — GET `/api/{org_id}/settings`
  Get organization settings
- `oo post settings` — POST `/api/{org_id}/settings`
  Update organization settings
  body required
- `oo get settings/v2` — GET `/api/{org_id}/settings/v2`
  List all resolved system settings
  query: user_id, category
- `oo post settings/v2` — POST `/api/{org_id}/settings/v2`
  Set organization-level setting
  body required
- `oo post settings/v2/user/<user_id>` — POST `/api/{org_id}/settings/v2/user/{user_id}`
  Set user-level setting
  body required
- `oo delete settings/v2/user/<user_id>/<key>` — DELETE `/api/{org_id}/settings/v2/user/{user_id}/{key}`
  Delete user-level setting
- `oo delete settings/v2/<key>` — DELETE `/api/{org_id}/settings/v2/{key}`
  Delete organization-level setting
- `oo get settings/v2/<key>` — GET `/api/{org_id}/settings/v2/{key}`
  Get resolved system setting
  query: user_id
- `oo get summary` — GET `/api/{org_id}/summary`
  Get organization summary

## Users

- `oo get users` — GET `/api/{org_id}/users`
  List organization users
- `oo post users` — POST `/api/{org_id}/users`
  Create new user
  body required
- `oo delete users/<email_id>` — DELETE `/api/{org_id}/users/{email_id}`
  Remove user from organization
- `oo post users/<email_id>` — POST `/api/{org_id}/users/{email_id}`
  Add user to organization
  body required
- `oo put users/<email_id>` — PUT `/api/{org_id}/users/{email_id}`
  Update user account
  body required

## Roles

- `oo get roles` — GET `/api/{org_id}/roles`
  List organization roles
- `oo post roles` — POST `/api/{org_id}/roles`
  Create custom role
  body required
- `oo delete roles/<role_id>` — DELETE `/api/{org_id}/roles/{role_id}`
  Delete custom role
- `oo put roles/<role_id>` — PUT `/api/{org_id}/roles/{role_id}`
  Update role permissions
  body required
- `oo get roles/<role_id>/permissions/<resource>` — GET `/api/{org_id}/roles/{role_id}/permissions/{resource}`
  Get role permissions for resource
- `oo get roles/<role_id>/users` — GET `/api/{org_id}/roles/{role_id}/users`
  Get users assigned to role

## Groups

- `oo get groups` — GET `/api/{org_id}/groups`
  List organization groups
- `oo post groups` — POST `/api/{org_id}/groups`
  Create user group
  body required
- `oo delete groups/<group_name>` — DELETE `/api/{org_id}/groups/{group_name}`
  Delete user group
- `oo get groups/<group_name>` — GET `/api/{org_id}/groups/{group_name}`
  Get group details
- `oo put groups/<group_name>` — PUT `/api/{org_id}/groups/{group_name}`
  Update user group
  body required

## Service accounts

- `oo get service_accounts` — GET `/api/{org_id}/service_accounts`
  List service accounts
- `oo post service_accounts` — POST `/api/{org_id}/service_accounts`
  Create service account
  body required
- `oo delete service_accounts/<email_id>` — DELETE `/api/{org_id}/service_accounts/{email_id}`
  Delete service account
- `oo put service_accounts/<email_id>` — PUT `/api/{org_id}/service_accounts/{email_id}`
  Update service account
  body required

## Cipher keys

- `oo post cipher_keys` — POST `/api/{org_id}/cipher_keys`
  Create encryption key
- `oo delete cipher_keys/<key_name>` — DELETE `/api/{org_id}/cipher_keys/{key_name}`
  Delete encryption key
- `oo put cipher_keys/<key_name>` — PUT `/api/{org_id}/cipher_keys/{key_name}`
  Update encryption key

- `oo get cipher_keys` — GET `/api/{org_id}/cipher_keys`
  List encryption keys
- `oo get cipher_keys/<key_name>` — GET `/api/{org_id}/cipher_keys/{key_name}`
  Get encryption key details

## Key-value store

- `oo get kv` — GET `/api/{org_id}/kv`
  List keys from key-value store
  query: prefix
- `oo delete kv/<key>` — DELETE `/api/{org_id}/kv/{key}`
  Delete key from key-value store
- `oo get kv/<key>` — GET `/api/{org_id}/kv/{key}`
  Get value from key-value store
- `oo post kv/<key>` — POST `/api/{org_id}/kv/{key}`
  Store value in key-value store
  body required

## Short URLs

- `oo post short` — POST `/api/{org_id}/short`
  Create short URL
  body required
- `oo api GET /short/{org}/short/{short_id}` — GET `/short/{org_id}/short/{short_id}`
  Resolve short URL
  query: type

## Rate limits

- `oo get ratelimit/module_list` — GET `/api/{org_id}/ratelimit/module_list`
  List module rate limit rules
  query: org_id*, interval
- `oo get ratelimit/role_list` — GET `/api/{org_id}/ratelimit/role_list`
  List role-based rate limit rules
  query: org_id*, user_role*, interval
- `oo put ratelimit/update` — PUT `/api/{org_id}/ratelimit/update`
  Update rate limit rules
  query: org_id*, update_type*, user_role, interval
  body required

## Service streams

The spec lists these without the `/api` prefix while their own summaries include it; try
`/api/{org}/service_streams` first.

- `oo api GET /{org}/service_streams` — GET `/{org_id}/service_streams`
- `oo api GET /{org}/service_streams/_analytics` — GET `/{org_id}/service_streams/_analytics`
  GET /api/{org_id}/service_streams/_analytics
- `oo api POST /{org}/service_streams/_correlate` — POST `/{org_id}/service_streams/_correlate`
  POST /api/{org_id}/service_streams/_correlate
  body required
- `oo api GET /{org}/service_streams/config/identity` — GET `/{org_id}/service_streams/config/identity`
- `oo api PUT /{org}/service_streams/config/identity` — PUT `/{org_id}/service_streams/config/identity`
  body required

## Patterns

- `oo post streams/<stream_name>/patterns/extract` — POST `/api/{org_id}/streams/{stream_name}/patterns/extract`
  Extract patterns from search results
  body required

## MCP

- `oo api POST /.well-known/oauth-authorization-server` — POST `/.well-known/oauth-authorization-server`
  Handler for OAuth 2.0 Authorization Server Metadata (Non-Enterprise)
- `oo post mcp` — POST `/api/{org_id}/mcp`
  body required

## Clusters

- `oo get clusters` — GET `/api/clusters`
  List available clusters

## Health

- `oo api GET /healthz` — GET `/healthz`
  System health check
