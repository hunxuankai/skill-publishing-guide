"""Validate a standalone skill offline and emit its installation hash manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote, urlsplit
import warnings
import xml.etree.ElementTree as ET

from markdown_it import MarkdownIt
import yaml

DEFAULT_SKILL = Path(__file__).absolute().parents[1] / "skills" / "skill-publishing-guide"
SUPPORTED = {
    "agents": {".yaml", ".yml"},
    "scripts": {".py", ".ps1"},
    "references": {".md", ".json", ".xml", ".log", ".txt", ".yaml", ".yml"},
}
SEMVER = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?", re.ASCII
)
SECRET = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"
    r"|\bgh[pousr]_[A-Za-z0-9]{30,}\b"
    r"|\bgithub_pat_[A-Za-z0-9_]{30,}\b"
    r"|\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"
    r"|\bSPT_[A-Za-z0-9]{20,}\b"
)


class ValidationError(ValueError):
    """Diagnostics never contain parser excerpts or potential secret values."""


def reject_link(path: Path) -> os.stat_result:
    info = path.lstat()
    # Path.is_junction is absent in Python 3.10/3.11. lstat is non-following.
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValidationError(f"Linked/reparse entry refused: {path.name}")
    return info


def package_files(root: Path) -> list[Path]:
    files = []

    def visit(directory: Path) -> None:
        for entry in sorted(directory.iterdir()):
            info = reject_link(entry)
            relative = entry.relative_to(root)
            parts = relative.parts
            if "__pycache__" in parts:
                index = parts.index("__pycache__")
                if stat.S_ISDIR(info.st_mode) and index == len(parts) - 1:
                    visit(entry)
                    continue
                if (stat.S_ISREG(info.st_mode) and index == len(parts) - 2
                        and entry.suffix == ".pyc"):
                    continue
                raise ValidationError(f"Unexpected cache entry: {relative.as_posix()}")
            if parts[0] not in SUPPORTED and relative.as_posix() != "SKILL.md":
                raise ValidationError(f"Unexpected package entry: {relative.as_posix()}")
            if stat.S_ISDIR(info.st_mode):
                if relative.as_posix() == "SKILL.md":
                    raise ValidationError("SKILL.md must be a file")
                visit(entry)
            elif stat.S_ISREG(info.st_mode):
                if (relative.as_posix() != "SKILL.md"
                        and (len(parts) < 2 or entry.suffix not in SUPPORTED[parts[0]])):
                    raise ValidationError(f"Unsupported package file: {relative.as_posix()}")
                files.append(entry)
            else:
                raise ValidationError(f"Unexpected non-file entry: {relative.as_posix()}")

    visit(root)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def load_yaml(text: str, label: str):
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        raise ValidationError(f"Invalid YAML: {label}") from None


def reject_json_constant(value: str):
    raise ValueError("Non-finite JSON number")


def markdown_destinations(text: str):
    """Extract actual CommonMark link and image tokens, excluding code."""
    parser = MarkdownIt("commonmark")
    # Preserve all destinations for our boundary checks rather than letting
    # renderer-oriented scheme filtering silently turn a link into plain text.
    parser.validateLink = lambda destination: True

    def destinations(tokens):
        for token in tokens:
            if token.type == "link_open":
                yield token.attrGet("href")
            elif token.type == "image":
                yield token.attrGet("src")
            if token.children:
                yield from destinations(token.children)

    yield from destinations(parser.parse(text))


def check(root: Path) -> dict:
    root = Path(os.path.abspath(root.expanduser()))
    for ancestor in (root, *root.parents):
        if ancestor.exists() or ancestor.is_symlink():
            reject_link(ancestor)
    if not root.is_dir():
        raise ValidationError("Skill directory does not exist")
    files = package_files(root)
    skill = root / "SKILL.md"
    if skill not in files:
        raise ValidationError("SKILL.md is required")
    texts = {}
    manifest = []
    for path in files:
        label = path.relative_to(root).as_posix()
        data = path.read_bytes()
        try:
            text = data.decode("utf-8-sig")
        except UnicodeError:
            raise ValidationError(f"Unsupported text encoding: {label}") from None
        if SECRET.search(text):
            raise ValidationError(f"Potential secret detected: {label}")
        texts[path] = text
        manifest.append({"path": label, "sha256": hashlib.sha256(data).hexdigest()})
        try:
            if path.suffix == ".py":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    compile(text, label, "exec", dont_inherit=True)
            elif path.suffix == ".json":
                json.loads(text, parse_constant=reject_json_constant)
            elif path.suffix == ".xml":
                ET.fromstring(text)
            elif path.suffix in {".yaml", ".yml"}:
                load_yaml(text, label)
        except SyntaxError:
            raise ValidationError(f"Invalid Python syntax: {label}") from None
        except (ValueError, ET.ParseError) as error:
            if isinstance(error, ValidationError):
                raise
            kind = "XML" if path.suffix == ".xml" else "JSON"
            raise ValidationError(f"Invalid {kind}: {label}") from None
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|$)", texts[skill], re.S)
    if not frontmatter:
        raise ValidationError("SKILL.md requires YAML frontmatter")
    metadata = load_yaml(frontmatter.group(1), "SKILL.md")
    if not isinstance(metadata, dict):
        raise ValidationError("SKILL.md YAML must be a mapping")
    name = metadata.get("name")
    if (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
            or len(name) > 64 or name != root.name):
        raise ValidationError("Skill name must be lowercase kebab-case and match its directory")
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ValidationError("Skill description must be a nonempty string")
    extra = metadata.get("metadata")
    version = extra.get("version") if isinstance(extra, dict) else None
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise ValidationError("metadata.version must be a SemVer string")
    references = []
    file_set = set(files)
    for path, text in texts.items():
        if path.suffix != ".md":
            continue
        for destination in markdown_destinations(text):
            try:
                url = urlsplit(destination)
                if url.scheme.lower() in {"http", "https", "mailto"}:
                    continue
                if url.scheme or url.netloc:
                    raise ValueError
                relative = unquote(url.path, errors="strict")
                if not relative:
                    continue
                if "\\" in relative or "\0" in relative or relative.startswith("/"):
                    raise ValueError
                linked = Path(os.path.abspath(path.parent / relative))
                if not linked.is_relative_to(root) or linked not in file_set:
                    raise ValueError
            except (ValueError, UnicodeError):
                raise ValidationError(f"Missing, escaping or unsupported local reference in: {path.relative_to(root).as_posix()}") from None
            references.append({"from": path.relative_to(root).as_posix(),
                               "path": linked.relative_to(root).as_posix()})
    return {"name": name, "version": version, "files": manifest,
            "local_references": references}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_path", nargs="?", type=Path, default=DEFAULT_SKILL)
    parser.add_argument("--json", action="store_true", dest="json_mode")
    args = parser.parse_args()
    try:
        result = check(args.skill_path)
    except (ValidationError, OSError) as error:
        # OS exceptions may quote untrusted content; only our diagnostics are printed.
        message = str(error) if isinstance(error, ValidationError) else "Cannot read package entries"
        print(f"FAIL: {message}", file=sys.stderr)
        return 1
    if args.json_mode:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"PASS: {result['name']} {result['version']}; {len(result['files'])} files, "
              f"{len(result['local_references'])} local references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
