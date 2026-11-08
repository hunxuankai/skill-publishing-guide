"""Exercise the new repository's real maintenance entrypoints in isolated roots."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAME = "skill-publishing-guide"


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def make_fixture(tmp_path):
    repo = tmp_path / "维护仓库"
    tools = repo / "tools"
    tools.mkdir(parents=True)
    for filename in ("check_skill.py", "install-local.ps1"):
        source = ROOT / "tools" / filename
        if source.is_file():
            shutil.copy2(source, tools / filename)
    source = repo / "skills" / NAME
    (source / "references").mkdir(parents=True)
    (source / "SKILL.md").write_text(
        '---\nname: skill-publishing-guide\ndescription: Controlled install fixture.\n'
        'metadata:\n  version: "1.0.0"\n---\n\n[Note](references/note.md)\n', encoding="utf-8")
    (source / "references/note.md").write_text("# 受控说明\n\n原版内容。\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(USERPROFILE=str(tmp_path / "host-user"),
               LOCALAPPDATA=str(tmp_path / "local-data"),
               PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    return repo, source, env


def install(repo, env, *arguments):
    return subprocess.run(
        ["pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-File",
         str(repo / "tools/install-local.ps1"), "-Python", sys.executable, *arguments],
        cwd=repo, env=env, capture_output=True, text=True, encoding="utf-8", timeout=40)


def test_preview_install_and_noop_use_new_skill_directory(tmp_path):
    repo, source, env = make_fixture(tmp_path)
    parent = Path(env["USERPROFILE"]) / ".agents/skills"
    target = parent / NAME
    backups = Path(env["LOCALAPPDATA"]) / "SkillBackups" / NAME
    result = install(repo, env, "-DryRun")
    assert result.returncode == 0, result.stdout + result.stderr
    assert not parent.exists()
    assert not backups.exists()
    result = install(repo, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert hashes(target) == hashes(source)
    assert sorted(p.name for p in parent.iterdir()) == [NAME]
    before = {p.relative_to(target): p.stat().st_mtime_ns for p in target.rglob("*") if p.is_file()}
    result = install(repo, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert {p.relative_to(target): p.stat().st_mtime_ns for p in target.rglob("*") if p.is_file()} == before
    assert not backups.exists()


def test_update_backs_up_named_package_and_preserves_unexpected_files(tmp_path):
    repo, source, env = make_fixture(tmp_path)
    target = Path(env["USERPROFILE"]) / ".agents/skills" / NAME
    backups = Path(env["LOCALAPPDATA"]) / "SkillBackups" / NAME
    first = install(repo, env)
    assert first.returncode == 0, first.stdout + first.stderr
    original = hashes(target)
    entry = source / "SKILL.md"
    entry.write_text(entry.read_text(encoding="utf-8").replace('"1.0.0"', '"1.0.1"'), encoding="utf-8")
    (source / "references/note.md").write_text("# 受控说明\n\n新版本内容。\n", encoding="utf-8")
    changed = install(repo, env)
    assert changed.returncode == 0, changed.stdout + changed.stderr
    copies = list(backups.glob("*/" + NAME))
    assert len(copies) == 1
    assert hashes(copies[0]) == original
    assert hashes(target) == hashes(source)
    (target / "local-note.md").write_text("Keep this user's note.", encoding="utf-8")
    before = hashes(target)
    before_backups = hashes(backups)
    refused = install(repo, env)
    assert refused.returncode != 0
    assert hashes(target) == before
    assert hashes(backups) == before_backups


def test_invalid_source_does_not_create_installation(tmp_path):
    repo, source, env = make_fixture(tmp_path)
    (source / "references/note.md").write_text("[Missing](outside.md)\n", encoding="utf-8")
    refused = install(repo, env)
    assert refused.returncode != 0
    assert not (Path(env["USERPROFILE"]) / ".agents/skills").exists()
    assert not (Path(env["LOCALAPPDATA"]) / "SkillBackups").exists()


def test_default_checker_manifest_matches_distributable_files():
    source = ROOT / "skills" / NAME
    result = subprocess.run([sys.executable, str(ROOT / "tools/check_skill.py"), "--json"],
                            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["name"] == NAME
    assert {item["path"]: item["sha256"] for item in manifest["files"]} == hashes(source)
    assert manifest["local_references"]
