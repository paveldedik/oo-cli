from pathlib import Path

import pytest

from oo_cli import skill
from oo_cli.client import OOError


def test_install_copies_the_skill(tmp_path: Path) -> None:
    target = skill.install(tmp_path)
    assert target == tmp_path / "openobserve"
    assert (target / "SKILL.md").is_file()
    assert (target / "references" / "endpoints.md").is_file()


def test_install_refuses_to_overwrite(tmp_path: Path) -> None:
    skill.install(tmp_path)
    with pytest.raises(OOError, match="already exists"):
        skill.install(tmp_path)
    assert skill.install(tmp_path, force=True)


def test_update_replaces_what_is_there(tmp_path: Path) -> None:
    target = skill.install(tmp_path)
    stale = target / "references" / "gone.md"
    stale.write_text("old")
    skill.update(tmp_path)
    assert not stale.exists()
    assert (target / "SKILL.md").is_file()


def test_update_without_an_installation(tmp_path: Path) -> None:
    with pytest.raises(OOError, match="does not exist"):
        skill.update(tmp_path)


def test_a_directory_that_is_not_a_skill_is_left_alone(tmp_path: Path) -> None:
    (tmp_path / "openobserve").mkdir()
    (tmp_path / "openobserve" / "notes.txt").write_text("mine")
    with pytest.raises(OOError, match="does not look like a skill"):
        skill.install(tmp_path, force=True)
