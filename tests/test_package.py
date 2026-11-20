import gzip
import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PluginPackageTests(unittest.TestCase):
    def test_manifest_and_skill_match_plugin_layout(self):
        manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "chinese-ui-pack")
        self.assertRegex(manifest["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertEqual(manifest["version"], "1.0.0")
        skill = ROOT / "skills" / "localize-ui" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^name: localize-ui$")
        self.assertRegex(text, r"(?m)^description: .+")

    def test_bundle_contains_one_consistent_translation_payload(self):
        payload_path = ROOT / "skills" / "localize-ui" / "scripts" / "zh-CN.json.gz"
        script_path = ROOT / "skills" / "localize-ui" / "scripts" / "patch.py"
        payload = json.loads(gzip.decompress(payload_path.read_bytes()))
        self.assertEqual(payload["version"], "2.34.0")
        self.assertEqual(len(payload["original"]), 64)
        self.assertEqual(len(payload["chinese"]), 64)
        self.assertGreater(len(payload["edits"]), 0)
        self.assertIn("PAYLOAD = Path(__file__).with_name",
                      script_path.read_text(encoding="utf-8"))

    def test_skill_and_double_click_installers_share_identical_payloads(self):
        for relative in ("patch.py", "zh-CN.json.gz"):
            skill_file = ROOT / "skills" / "localize-ui" / "scripts" / relative
            installer_copy = ROOT / "scripts" / relative
            self.assertEqual(
                hashlib.sha256(skill_file.read_bytes()).digest(),
                hashlib.sha256(installer_copy.read_bytes()).digest(),
                relative,
            )

    def test_command_files_target_the_bundled_installer(self):
        install = (ROOT / "scripts" / "install-zh-cn.cmd").read_text(encoding="utf-8")
        restore = (ROOT / "scripts" / "restore-english.cmd").read_text(encoding="utf-8")
        self.assertIn("patch.py\" install", install)
        self.assertIn("patch.py\" restore", restore)

    def test_no_automatic_hooks_or_external_tools_are_configured(self):
        self.assertFalse((ROOT / "hooks.json").exists())
        self.assertFalse((ROOT / "mcp_config.json").exists())
        self.assertFalse((ROOT / "agents").exists())

    def test_upstream_notice_and_mit_licenses_are_present(self):
        self.assertIn("MIT License", (ROOT / "LICENSE").read_text(encoding="utf-8"))
        self.assertIn("MIT License", (ROOT / "LICENSE.upstream").read_text(encoding="utf-8"))
        self.assertIn("Antigravity Chinese Localization",
                      (ROOT / "NOTICE.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
