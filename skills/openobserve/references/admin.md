# Organizations, users and the rest

## Organizations

```bash
oo get organizations                 # /api/organizations - no org in the path
oo post organizations -d '{"name":"team-b"}'
oo put rename -d '{"new_name":"Platform"}'
oo get summary                       # ingestion, storage, stream and function counts
```

`oo get organizations` is the first call to make against an unfamiliar instance: it proves
the credential works and lists the org identifiers `--org` accepts. A root user sees every
organization. `oo get clusters` lists clusters in a distributed deployment.

## Ingestion tokens

```bash
oo get passcode        # the current ingestion token for this user and org
oo put passcode        # rotate it - every ingester using the old one breaks
oo get rumtoken
oo post rumtoken       # create the first RUM token
oo put rumtoken        # rotate it
```

These return credentials. Never print one into a chat, a commit or a log; redirect to a file
or into an environment variable.

## Settings

```bash
oo get settings
oo post settings -d '{"scrape_interval": 15}'
```

Org settings hold `scrape_interval`, `trace_id_field_name` / `span_id_field_name`,
`max_series_per_query`, `min_auto_refresh_interval`, `toggle_ingestion_logs`,
`usage_stream_enabled`, `enable_streaming_search`, `streaming_aggregation_enabled`, the two
theme colours and `cross_links`.

A newer key-value system sits alongside it, resolving system -> org -> user:

```bash
oo get settings/v2                         # everything, resolved
oo get settings/v2 --category ui
oo get settings/v2/<key> --user_id <id>    # the value this user actually sees
oo post settings/v2 -d '{"setting_key":"...","setting_value":...,"setting_category":"ui"}'
oo post settings/v2/user/<user_id> -d '{"setting_key":"...","setting_value":...}'
oo delete settings/v2/<key>                # falls back to the system default
```

## Users, roles, groups, service accounts

```bash
oo get users
oo post users -d '{"email":"a@example.com","password":"...","role":"admin","first_name":"A","last_name":"B"}'
oo put users/<email> -d '{"first_name":"A"}'
oo post users/<email> -d '{"role":"member"}'      # add an existing user to this org
oo delete users/<email>                           # removes from the org

oo get roles                                      # enterprise RBAC
oo get roles/<role_id>/permissions/<resource>
oo get roles/<role_id>/users
oo post roles -d '{"role":"readonly"}'
oo put roles/<role_id> -f permissions.json

oo get groups
oo post groups -d '{"name":"platform"}'
oo put groups/<group_name> -d '{"add_users":["a@example.com"],"add_roles":["readonly"]}'
```

A service account is a user without a password, used for automation; its token comes from
`passcode` once the account exists.

```bash
oo get service_accounts
oo post service_accounts -d '{"email":"ci@example.com","first_name":"CI","last_name":"bot"}'
oo delete service_accounts/<email>
```

Roles and groups are enterprise features and answer with an error on OSS builds. Creating or
deleting users changes who can reach the data - always confirm first.

## Key-value store

A small per-org store the UI uses and you can too:

```bash
oo get kv                       # every key
oo get kv --prefix dashboard_
oo get kv/<key>                 # the raw value, not JSON
oo post kv/<key> -d 'some text'
oo delete kv/<key>
```

## Short URLs

```bash
oo post short -d '{"original_url":"https://openobserve.example.com/web/logs?..."}'
oo api GET /short/default/short/<short_id> --type ui     # resolve without redirecting
```

## Cipher keys and rate limits

`cipher_keys` (encryption key management) and `ratelimit` (per-module and per-role request
limits) are enterprise-only:

```bash
oo get cipher_keys
oo get ratelimit/module_list --org_id default
oo get ratelimit/role_list --org_id default --user_role admin
```

## Health and the spec

```bash
oo api GET /healthz            # {"status":"ok"}, the one endpoint needing no credential
oo spec paths                  # every path this build serves
oo spec refresh                # after an upgrade
```

## MCP

Recent builds expose `POST /api/{org}/mcp`, an MCP server over the same API. The endpoint
carries per-operation hints (which operations are exposed, which need confirmation) that this
skill's guidance is drawn from. Check `oo spec paths mcp` before assuming it is there.
