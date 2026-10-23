"""Simple terminal interface for manifest creation and verification."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import save_manifest, verify_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic directory integrity checks")
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("make", help="Create SHA-256 manifest")
    make.add_argument("directory", type=Path)
    make.add_argument("output", type=Path)
    verify = sub.add_parser("verify", help="Compare directory against manifest")
    verify.add_argument("directory", type=Path)
    verify.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "make":
            manifest = save_manifest(args.directory, args.output)
            print(f"Manifest created for {len(manifest['files'])} files")
            return 0
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        changes = verify_manifest(args.directory, manifest)
        print(json.dumps(changes, indent=2))
        return 1 if any(changes.values()) else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
