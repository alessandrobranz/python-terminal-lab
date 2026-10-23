"""Build and verify deterministic SHA-256 directory manifests."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stat
from pathlib import Path

HASH_RE = re.compile(r"[0-9a-f]{64}\Z")


def _walk_regular_files(root: Path) -> dict[str, Path]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Root must be a real directory")
    results: dict[str, Path] = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        base_path = Path(base)
        dirs.sort()
        files.sort()
        for name in dirs:
            if (base_path / name).is_symlink():
                raise ValueError("Symbolic links are not supported")
        for name in files:
            path = base_path / name
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
                raise ValueError("Only regular files are supported")
            results[path.relative_to(root).as_posix()] = path
    return results


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_manifest(root: Path) -> dict:
    root = Path(root).resolve()
    entries = _walk_regular_files(root)
    return {
        "schema_version": 1,
        "files": [
            {"path": name, "size": entries[name].stat().st_size, "sha256": _digest(entries[name])}
            for name in sorted(entries)
        ],
    }


def save_manifest(root: Path, output: Path) -> dict:
    root = Path(root).resolve()
    output = Path(output).resolve()
    if output == root or root in output.parents:
        raise ValueError("Manifest output must be outside the indexed directory")
    manifest = create_manifest(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _valid_paths(manifest: dict) -> dict[str, tuple[int, str]]:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
        raise ValueError("Invalid manifest schema")
    expected = {}
    for item in manifest["files"]:
        if not isinstance(item, dict):
            raise ValueError("Invalid manifest entry")
        path, size, digest = item.get("path"), item.get("size"), item.get("sha256")
        if (not isinstance(path, str) or not path or "\\" in path or
            path.startswith("/") or any(s in ("", ".", "..") for s in path.split("/")) or
            path in expected or type(size) is not int or size < 0 or
            not isinstance(digest, str) or not HASH_RE.fullmatch(digest)):
            raise ValueError("Invalid manifest entry")
        expected[path] = (size, digest)
    return expected


def verify_manifest(root: Path, manifest: dict) -> dict[str, list[str]]:
    expected = _valid_paths(manifest)
    current = _walk_regular_files(Path(root).resolve())
    missing = sorted(expected.keys() - current.keys())
    unexpected = sorted(current.keys() - expected.keys())
    modified = sorted(
        name for name in expected.keys() & current.keys()
        if current[name].stat().st_size != expected[name][0]
        or not hmac.compare_digest(_digest(current[name]), expected[name][1])
    )
    return {"missing": missing, "modified": modified, "unexpected": unexpected}
