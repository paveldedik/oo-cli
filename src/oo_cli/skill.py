"""The agent skill that ships with the CLI, and installing it where agents look.

The files live in `skills/openobserve` in the repository and are copied into the wheel,
so an installed CLI can hand them out without fetching anything.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from oo_cli.client import OOError

NAME = "openobserve"

#: The agent-agnostic skills directory; `--dir` points at any other one.
DEFAULT_DIR = Path.home() / ".agents" / "skills"


def source() -> Path:
    """The bundled copy of the skill."""
    packaged = Path(__file__).with_name("_skill")
    if packaged.is_dir():
        return packaged
    checkout = Path(__file__).parents[2] / "skills" / NAME
    if checkout.is_dir():
        return checkout
    raise OOError("this installation carries no skill files")


def install(directory: Path | None = None, force: bool = False) -> Path:
    target = (directory or DEFAULT_DIR) / NAME
    if target.exists() and not force:
        raise OOError(f"{target} already exists, run `oo skill update` to replace it")
    return _replace(target)


def update(directory: Path | None = None) -> Path:
    target = (directory or DEFAULT_DIR) / NAME
    if not target.exists():
        raise OOError(f"{target} does not exist, run `oo skill install` first")
    return _replace(target)


def _replace(target: Path) -> Path:
    """Copy the bundled skill over the target, which only ever holds a copy of it."""
    if target.exists() and not (target / "SKILL.md").is_file():
        raise OOError(f"{target} exists and does not look like a skill, refusing to replace it")
    files = source()
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(files, target)
    return target
