# Design notes

## JSON schema

```json
{
  "schema_version": 1,
  "files": [
    {"path": "hello.txt", "size": 42, "sha256": "64 lowercase hex characters"}
  ]
}
```

The paths are UTF-8 relative paths with forward slashes. The list is lexicographically sorted and the result is deterministic for an unchanged directory.

## Verification

1. Validate the manifest structure (including duplicate paths and traversal).
2. Enumerate regular files without following symbolic links.
3. Report missing names, unexpected names, and content/size mismatches separately.
4. Exit 0 only if all categories are empty.

The hashing algorithm reads in fixed-size chunks to avoid buffering entire files.

## Scope

Symlinks and nonregular files are deliberately unsupported to simplify semantics. The tool does not authenticate the source manifest or guarantee a consistent snapshot of files changing during the scan.

Synthetic sample data only; no employer information.
