import gzip
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
        self.assertEqual(manifest["version"], "1.0.1")
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

    def test_installer_and_payload_are_bundled_once(self):
        for relative in ("patch.py", "zh-CN.json.gz"):
            self.assertTrue((ROOT / "skills" / "localize-ui" / "scripts" / relative).is_file())
            self.assertFalse((ROOT / "scripts" / relative).exists(), relative)

    def test_command_files_target_the_bundled_installer(self):
        for name, action in (("install-zh-cn.cmd", "install"),
                             ("restore-english.cmd", "restore")):
            raw = (ROOT / "scripts" / name).read_bytes()
            text = raw.decode("utf-8")
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), name)
            self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"), name)
            self.assertIn(r"%~dp0..\skills\localize-ui\scripts\patch.py", text)
            self.assertIn(f'"%SCRIPT%" {action}', text)
            self.assertIn("py -3", text)
            self.assertIn("python", text)

    def test_skill_uses_absolute_script_path(self):
        text = (ROOT / "skills" / "localize-ui" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(r"chinese-ui-pack\skills\localize-ui\scripts\patch.py", text)
        self.assertNotRegex(text, r"(?m)^\s+python -X utf8 scripts/patch\.py")

    def test_manifest_has_only_supported_fields(self):
        manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        supported = {"name", "description", "logo", "suggestedPrompts", "displayName",
                     "version", "author", "homepage", "repository", "disabled"}
        self.assertLessEqual(set(manifest), supported)

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
