# Python Terminal Lab — Directory Integrity Checker

A small **Python 3.10+ command-line application** that inventories a directory using SHA-256 and detects modified, missing, or unexpected files.

This is an independently written, general-purpose example using **only Python's standard library at runtime**. It contains no employer data or workplace code.

## Features

- Deterministic JSON manifests sorted by relative path
- SHA-256 checksums computed in streamed chunks
- Compare manifests against current files (missing, modified, unexpected)
- Reject directory symlinks, file symlinks, nonregular files and unsafe manifest paths
- Simple CLI exit codes: 0 = success, 1 = changes, 2 = invalid input
- Automated tests with Python unittest and GitHub Actions

## Quick start

From the repository root:

\`\`\`sh
PYTHONPATH=src python -m fileaudit make examples/files manifest.json
PYTHONPATH=src python -m fileaudit verify examples/files manifest.json
PYTHONPATH=src python -m unittest discover -s tests -v
\`\`\`

The manifest must be outside the indexed directory. Edit a sample file and rerun verification to see the mismatch reported.

## CLI usage

\`\`\`text
python -m fileaudit make DIRECTORY MANIFEST_JSON
python -m fileaudit verify DIRECTORY MANIFEST_JSON
\`\`\`

## Design notes

[Read the engineering notes](docs/design.md) for the manifest format, boundary checks, and limitations.

### Constraints

This is a **learning/demo tool**, not a replacement for signed artifact validation. It does not cryptographically authenticate the manifest itself, protect against concurrent file modifications, or detect malicious changes to both the directory and manifest. Use a trusted manifest and do not traverse untrusted writable directories.

No open-source license has been granted for redistribution.
