import gzip
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch as mock_patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "skills" / "localize-ui" / "scripts"))
import patch


def make_asar(files):
    offset = 0
    entries = {}
    payload = []
    for name, content in files.items():
        parts = name.split("/")
        node = entries
        for part in parts[:-1]:
            node = node.setdefault(part, {"files": {}})["files"]
        node[parts[-1]] = {"size": len(content), "offset": str(offset)}
        payload.append(content)
        offset += len(content)

    header_text = json.dumps({"files": entries}, separators=(",", ":")).encode()
    padding = (-len(header_text)) % 4
    header_size = 8 + len(header_text) + padding
    preamble = struct.pack("<4I", 4, header_size, 4 + len(header_text) + padding,
                           len(header_text))
    return preamble + header_text + bytes(padding) + b"".join(payload)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "Antigravity.exe").write_bytes(b"test launcher")
        (self.root / "resources").mkdir()
        self.target = self.root / "resources" / "app.asar"
        self.original = make_asar({
            "package.json": b'{"version":"2.34.0"}',
            "dist/label.js": b"File",
            "unchanged.bin": bytes(range(16)),
        })
        self.target.write_bytes(self.original)
        self.payload_file = self.root / "zh-CN.json.gz"
        payload = {
            "version": patch.VERSION,
            "original": patch.sha(self.original),
            "edits": {"dist/label.js": [[0, 4, "文件"]]},
        }
        self.localized = patch.translate(self.original, payload)
        payload["chinese"] = patch.sha(self.localized)
        self.write_payload(payload)
        self.payload_patch = mock_patch.object(patch, "PAYLOAD", self.payload_file)
        self.payload_patch.start()

    def tearDown(self):
        self.payload_patch.stop()
        self.temp.cleanup()

    def write_payload(self, payload):
        self.payload_file.write_bytes(
            gzip.compress(json.dumps(payload).encode("utf-8"), mtime=0)
        )

    def test_install_is_atomic_versioned_and_restorable(self):
        self.assertIn("英文原版", patch.run("status", self.root))
        self.assertIn("已安装", patch.run("install", self.root, fixture=True))
        self.assertEqual(self.target.read_bytes(), self.localized)
        self.assertEqual(
            (self.root / "resources" / patch.BACKUP_NAME).read_bytes(),
            self.original,
        )
        self.assertIn("已经安装", patch.run("install", self.root, fixture=True))
        self.assertIn("已恢复", patch.run("restore", self.root, fixture=True))
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_modified_app_is_left_untouched(self):
        updated = patch.Archive(self.original).replace(
            {"package.json": b'{"version":"2.34.1"}'}
        )
        self.target.write_bytes(updated)
        with self.assertRaisesRegex(ValueError, "2.34.1"):
            patch.run("install", self.root, fixture=True)
        self.assertEqual(self.target.read_bytes(), updated)
        self.assertFalse((self.root / "resources" / patch.BACKUP_NAME).exists())

    def test_running_app_blocks_installation(self):
        with mock_patch.object(patch, "desktop_is_running", return_value=True):
            with self.assertRaisesRegex(ValueError, "请先正常退出"):
                patch.run("install", self.root)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertFalse((self.root / "resources" / patch.BACKUP_NAME).exists())

    def test_tampered_payload_fails_before_writing(self):
        payload = gzip.decompress(self.payload_file.read_bytes())
        data = json.loads(payload)
        data["chinese"] = "0" * 64
        self.write_payload(data)
        with self.assertRaisesRegex(ValueError, "汉化文件验证失败"):
            patch.run("install", self.root, fixture=True)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertFalse((self.root / "resources" / patch.BACKUP_NAME).exists())

    def test_out_of_bounds_translation_is_rejected(self):
        bad = {
            "edits": {"dist/label.js": [[0, 100, "越界"]]},
        }
        with self.assertRaisesRegex(ValueError, "文字位置有误"):
            patch.translate(self.original, bad)


if __name__ == "__main__":
    unittest.main()
