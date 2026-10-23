import json
import tempfile
import unittest
from pathlib import Path

from fileaudit.cli import main
from fileaudit.core import create_manifest, save_manifest, verify_manifest


class FileAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "items"
        self.root.mkdir()
        (self.root / "b.txt").write_text("beta", encoding="utf-8")
        (self.root / "a.txt").write_text("alpha", encoding="utf-8")

    def test_manifest_is_sorted_and_deterministic(self):
        a = create_manifest(self.root)
        self.assertEqual(a, create_manifest(self.root))
        self.assertEqual([x["path"] for x in a["files"]], ["a.txt", "b.txt"])

    def test_verify_unchanged(self):
        manifest = create_manifest(self.root)
        self.assertEqual(verify_manifest(self.root, manifest), {"missing": [], "modified": [], "unexpected": []})

    def test_modified_same_size_detected(self):
        m = create_manifest(self.root)
        (self.root / "a.txt").write_text("ALPHA", encoding="utf-8")
        self.assertEqual(verify_manifest(self.root, m)["modified"], ["a.txt"])

    def test_missing_and_unexpected(self):
        m = create_manifest(self.root)
        (self.root / "a.txt").unlink()
        (self.root / "c.txt").write_text("added", encoding="utf-8")
        delta = verify_manifest(self.root, m)
        self.assertEqual(delta["missing"], ["a.txt"])
        self.assertEqual(delta["unexpected"], ["c.txt"])

    def test_nested_paths(self):
        nested = self.root / "folder"
        nested.mkdir()
        (nested / "note.txt").write_text("note", encoding="utf-8")
        self.assertIn("folder/note.txt", [x["path"] for x in create_manifest(self.root)["files"]])

    def test_reject_output_inside_root(self):
        with self.assertRaises(ValueError):
            save_manifest(self.root, self.root / "manifest.json")

    def test_invalid_manifest_traversal(self):
        m = create_manifest(self.root)
        m["files"][0]["path"] = "../secret"
        with self.assertRaises(ValueError):
            verify_manifest(self.root, m)

    def test_invalid_duplicate_path(self):
        m = create_manifest(self.root)
        m["files"].append(dict(m["files"][0]))
        with self.assertRaises(ValueError):
            verify_manifest(self.root, m)

    def test_invalid_manifest_type(self):
        with self.assertRaises(ValueError):
            verify_manifest(self.root, {"schema_version": 1, "files": [{"path": "x", "size": True, "sha256": "0" * 64}]})

    def test_reject_symlinks(self):
        (self.root / "link").symlink_to("a.txt")
        with self.assertRaises(ValueError):
            create_manifest(self.root)

    def test_cli_end_to_end(self):
        output = self.base / "manifest.json"
        self.assertEqual(main(["make", str(self.root), str(output)]), 0)
        self.assertEqual(main(["verify", str(self.root), str(output)]), 0)
        self.assertEqual(json.loads(output.read_text())["schema_version"], 1)
        (self.root / "a.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(main(["verify", str(self.root), str(output)]), 1)

    def test_cli_invalid_manifest_returns_two(self):
        manifest = self.base / "bad.json"
        manifest.write_text("not JSON", encoding="utf-8")
        self.assertEqual(main(["verify", str(self.root), str(manifest)]), 2)


if __name__ == "__main__":
    unittest.main()
