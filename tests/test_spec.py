from oo_cli.spec import Spec

TEMPLATES = {
    "/api/{org_id}/dashboards": ["get", "post"],
    "/api/{org_id}/dashboards/{dashboard_id}": ["get", "put", "delete"],
    "/api/{org_id}/alerts": ["get", "post"],
    "/api/v2/{org_id}/alerts": ["get", "post"],
    "/api/v2/{org_id}/alerts/{alert_id}": ["get", "put", "delete"],
    "/api/{org_id}/streams/{stream_name}": ["get"],
    "/api/organizations": ["get", "post"],
}


def test_prefers_v2_when_the_endpoint_exists_in_both() -> None:
    resolution = Spec(TEMPLATES).resolve("default", ["alerts"], "get")
    assert resolution.path == "/api/v2/default/alerts"
    assert resolution.matched


def test_falls_back_to_v1_when_v2_is_missing() -> None:
    resolution = Spec(TEMPLATES).resolve("default", ["dashboards"], "get")
    assert resolution.path == "/api/default/dashboards"
    assert resolution.matched


def test_matches_a_path_parameter() -> None:
    resolution = Spec(TEMPLATES).resolve("acme", ["streams", "app_logs"], "get")
    assert resolution.path == "/api/acme/streams/app_logs"
    assert resolution.matched


def test_version_follows_the_method() -> None:
    # DELETE only exists on the v2 collection item, POST only on the v1 collection.
    resolution = Spec(TEMPLATES).resolve("default", ["alerts", "7"], "delete")
    assert resolution.path == "/api/v2/default/alerts/7"


def test_unknown_resource_is_reported_as_unmatched_v1() -> None:
    resolution = Spec(TEMPLATES).resolve("default", ["widgets"], "get")
    assert resolution.path == "/api/default/widgets"
    assert not resolution.matched


def test_without_a_spec_only_the_known_v2_resources_go_to_v2() -> None:
    empty = Spec({})
    assert empty.resolve("default", ["alerts"], "get").path == "/api/v2/default/alerts"
    assert empty.resolve("default", ["dashboards"], "get").path == "/api/default/dashboards"


def test_an_endpoint_outside_an_organization_drops_the_org() -> None:
    resolution = Spec(TEMPLATES).resolve("default", ["organizations"], "get")
    assert resolution.path == "/api/organizations"
    assert resolution.matched
