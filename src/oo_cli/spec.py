"""The instance's own OpenAPI document, used to route a command to v1 or v2.

OpenObserve serves its spec at /api-doc/openapi.json, so the command surface follows
whatever version is deployed instead of a table we would have to maintain by hand.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from oo_cli.client import Client, OOError

SPEC_PATH = "/api-doc/openapi.json"
MAX_AGE_SECONDS = 7 * 24 * 3600

#: Resources that exist in both versions; used when the spec cannot be fetched.
V2_RESOURCES = frozenset({"alerts", "folders", "reports"})

_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


@dataclass(frozen=True)
class Resolution:
    path: str
    template: str | None

    @property
    def matched(self) -> bool:
        return self.template is not None


class Spec:
    def __init__(self, templates: dict[str, list[str]]) -> None:
        self.templates = templates

    def __bool__(self) -> bool:
        return bool(self.templates)

    def resolve(self, org: str, segments: list[str], method: str) -> Resolution:
        """Map command segments onto a concrete API path, preferring v2.

        A few endpoints (organizations, clusters) sit outside an organization, so an
        org-less path is the last candidate.
        """
        tail = "/".join(segments)
        v2, v1, global_ = f"/api/v2/{org}/{tail}", f"/api/{org}/{tail}", f"/api/{tail}"

        if not self.templates:
            return Resolution(v2 if segments and segments[0] in V2_RESOURCES else v1, None)

        for candidate in (v2, v1, global_):
            template = self._match(candidate, method)
            if template:
                return Resolution(candidate, template)
        return Resolution(v1, None)

    def _match(self, path: str, method: str) -> str | None:
        parts = path.strip("/").split("/")
        for template, methods in self.templates.items():
            if method.lower() not in methods:
                continue
            template_parts = template.strip("/").split("/")
            if len(template_parts) != len(parts):
                continue
            if all(
                t.startswith("{") and t.endswith("}") or t == p
                for t, p in zip(template_parts, parts)
            ):
                return template
        return None

    def paths(self, needle: str | None = None) -> list[tuple[str, list[str]]]:
        items = sorted(self.templates.items())
        if needle:
            items = [(p, m) for p, m in items if needle.lower() in p.lower()]
        return items


def load(client: Client, refresh: bool = False) -> Spec:
    """Return the cached spec, fetching it when missing, stale or forced."""
    cache = _cache_file(client.config.endpoint)
    if not refresh:
        cached = _read_cache(cache)
        if cached is not None:
            return Spec(cached)

    try:
        document = client.json("GET", SPEC_PATH)
    except OOError:
        cached = _read_cache(cache, ignore_age=True)
        return Spec(cached if cached is not None else {})

    templates = {
        path: [m for m in operations if m in _METHODS]
        for path, operations in document.get("paths", {}).items()
    }
    _write_cache(cache, client.config.endpoint, templates)
    return Spec(templates)


def _cache_file(endpoint: str) -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    digest = hashlib.sha1(endpoint.encode()).hexdigest()[:12]
    return Path(base) / "oo-cli" / f"spec-{digest}.json"


def _read_cache(path: Path, ignore_age: bool = False) -> dict[str, list[str]] | None:
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    if not ignore_age and time.time() - payload.get("fetched_at", 0) > MAX_AGE_SECONDS:
        return None
    return payload.get("templates")


def _write_cache(path: Path, endpoint: str, templates: dict[str, list[str]]) -> None:
    payload = {"endpoint": endpoint, "fetched_at": time.time(), "templates": templates}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
    except OSError:
        pass
