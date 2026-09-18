"""Command line entry point.

Commands are a transcription of the API: `oo get dashboards` is
`GET /api/{org}/dashboards`. Where the instance offers a v2 of an endpoint, the
v2 one is used; the spec module decides that, there is no version switch.
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

from oo_cli import __version__, spec as spec_module
from oo_cli.client import Client, HTTPError, OOError
from oo_cli.config import Config, ConfigError
from oo_cli.timeutil import TimeError, to_micros

VERBS = ("get", "post", "put", "patch", "delete")

EPILOG = """\
examples:
  oo get dashboards
  oo get alerts --folder default          -> /api/v2/{org}/alerts?folder=default
  oo get streams/sp_metrics
  oo post alerts -f alert.json
  oo delete dashboards/0194f0e1 --folder default
  oo search --sql "select * from cloudwatch_logs limit 10" --from -30m
  oo api GET /api/{org}/prometheus/api/v1/query --query "up"

environment:
  OO_ENDPOINT  default http://localhost:5080
  OO_ORG       default "default"
  OO_TOKEN     base64 of "email:token", sent as HTTP basic auth
  OO_USER      alternative to OO_TOKEN, together with OO_PASSWORD
  OO_TIMEOUT   seconds, default 60

Any other --name value or --name=value is passed through as a query parameter.
"""


class UsageError(Exception):
    pass


def main(argv: list[str] | None = None) -> int:
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except UsageError as exc:
        print(f"oo: {exc}", file=sys.stderr)
        return 2
    except (ConfigError, TimeError) as exc:
        print(f"oo: {exc}", file=sys.stderr)
        return 2
    except HTTPError as exc:
        print(f"oo: {exc}", file=sys.stderr)
        _emit(exc.response, raw=False, stream=sys.stderr)
        return 1
    except OOError as exc:
        print(f"oo: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0


def run(argv: list[str]) -> int:
    parser = _parser()
    args, extras = parser.parse_known_args(_glue_offsets(argv))
    if not args.command:
        parser.print_help()
        return 2

    config = Config.from_env(endpoint=args.endpoint, org=args.org, timeout=args.timeout)
    with Client(config) as client:
        if args.command == "spec":
            return _run_spec(client, args, extras)
        if args.command == "search":
            return _run_search(client, args, extras)
        if args.command == "api":
            return _run_api(client, args, extras)
        return _run_verb(client, args, extras)


#: Options whose value starts with a minus (--from -30m), which argparse reads as an option.
_OFFSET_OPTIONS = ("--from", "--to")


def _glue_offsets(argv: list[str]) -> list[str]:
    glued: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        following = argv[index + 1] if index + 1 < len(argv) else None
        if token in _OFFSET_OPTIONS and following is not None and following.startswith("-"):
            glued.append(f"{token}={following}")
            index += 2
            continue
        glued.append(token)
        index += 1
    return glued


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oo",
        description="Talk to the OpenObserve API.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"oo {__version__}")
    parser.add_argument("--endpoint", help="OpenObserve base URL (env OO_ENDPOINT)")
    parser.add_argument("--org", help="organization (env OO_ORG)")
    parser.add_argument("--timeout", type=float, help="request timeout in seconds")
    parser.add_argument("--raw", action="store_true", help="print the response body unformatted")

    sub = parser.add_subparsers(dest="command")

    for verb in VERBS:
        p = sub.add_parser(
            verb,
            help=f"{verb.upper()} a resource, e.g. oo {verb} dashboards",
            allow_abbrev=False,
        )
        p.add_argument("resource", help='resource path under the org, e.g. "alerts" or "alerts/<id>"')
        _add_body_arguments(p)

    p = sub.add_parser("api", help="call any path verbatim", allow_abbrev=False)
    p.add_argument("method", help="HTTP method")
    p.add_argument("path", help="full path, e.g. /api/default/streams")
    _add_body_arguments(p)

    p = sub.add_parser("search", help="run a SQL search", allow_abbrev=False)
    p.add_argument("--sql", required=True, help="SQL query, e.g. select * from cloudwatch_logs")
    p.add_argument("--from", dest="start", default="-1h", help="start time, default -1h")
    p.add_argument("--to", dest="end", default="now", help="end time, default now")
    p.add_argument("--size", type=int, default=100, help="number of rows, default 100")
    p.add_argument("--offset", type=int, default=0, help="row offset, default 0")
    p.add_argument("--type", default="logs", help="stream type: logs, metrics or traces")

    p = sub.add_parser("spec", help="inspect the instance's OpenAPI document", allow_abbrev=False)
    p.add_argument("action", choices=("paths", "refresh"), help="list endpoints or refetch the spec")
    p.add_argument("needle", nargs="?", help="substring filter for paths")

    return parser


def _add_body_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-d", "--data", help='request body, @file or @- for stdin')
    parser.add_argument("-f", "--file", help="request body read from a file")


def _run_verb(client: Client, args: argparse.Namespace, extras: list[str]) -> int:
    segments = [s for s in args.resource.strip("/").split("/") if s]
    if not segments:
        raise UsageError("a resource is required, e.g. oo get dashboards")

    spec = spec_module.load(client)
    resolution = spec.resolve(client.config.org, segments, args.command)
    if spec and not resolution.matched:
        print(
            f"oo: {args.command.upper()} {resolution.path} is not in the spec, sending it anyway",
            file=sys.stderr,
        )
    response = client.request(
        args.command, resolution.path, params=_params(extras), body=_body(args)
    )
    _emit(response, args.raw)
    return 0


def _run_api(client: Client, args: argparse.Namespace, extras: list[str]) -> int:
    path = args.path if args.path.startswith("/") else "/" + args.path
    response = client.request(args.method, path, params=_params(extras), body=_body(args))
    _emit(response, args.raw)
    return 0


def _run_search(client: Client, args: argparse.Namespace, extras: list[str]) -> int:
    body = {
        "query": {
            "sql": args.sql,
            "start_time": to_micros(args.start),
            "end_time": to_micros(args.end),
            "from": args.offset,
            "size": args.size,
        }
    }
    params = [("type", args.type), *_params(extras)]
    response = client.request(
        "POST", f"/api/{client.config.org}/_search", params=params, body=json.dumps(body).encode()
    )
    _emit(response, args.raw)
    return 0


def _run_spec(client: Client, args: argparse.Namespace, extras: list[str]) -> int:
    if extras:
        raise UsageError(f"unexpected argument {extras[0]}")
    spec = spec_module.load(client, refresh=args.action == "refresh")
    if not spec:
        raise OOError("could not read the OpenAPI document from the instance")
    for path, methods in spec.paths(args.needle):
        print(f"{' '.join(sorted(methods)).upper():<28} {path}")
    return 0


def _params(extras: list[str]) -> list[tuple[str, str]]:
    """Turn leftover --name value / --name=value pairs into query parameters."""
    params: list[tuple[str, str]] = []
    index = 0
    while index < len(extras):
        token = extras[index]
        if not token.startswith("--"):
            raise UsageError(f"unexpected argument {token}")
        name, _, value = token[2:].partition("=")
        if not name:
            raise UsageError(f"unexpected argument {token}")
        if not _:
            following = extras[index + 1] if index + 1 < len(extras) else None
            if following is not None and not following.startswith("--"):
                value = following
                index += 1
            else:
                value = "true"
        params.append((name, value))
        index += 1
    return params


def _body(args: argparse.Namespace) -> bytes | None:
    data, file = getattr(args, "data", None), getattr(args, "file", None)
    if data and file:
        raise UsageError("use either -d or -f, not both")
    if file:
        data = "@" + file
    if not data:
        return None
    if not data.startswith("@"):
        return data.encode()
    source = data[1:]
    if source == "-":
        return sys.stdin.buffer.read()
    try:
        with open(source, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise UsageError(f"cannot read {source}: {exc}") from exc


def _emit(response: httpx.Response, raw: bool, stream=sys.stdout) -> None:
    text = response.text
    if not text.strip():
        return
    if not raw and "json" in response.headers.get("content-type", ""):
        try:
            text = json.dumps(response.json(), indent=2, ensure_ascii=False)
        except ValueError:
            pass
    print(text, file=stream)
