"""Offline installer for the Windows Antigravity 2.34.0 Chinese UI."""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


VERSION = "2.34.0"
PAYLOAD = Path(__file__).with_name("zh-CN.json.gz")
BACKUP_NAME = f"app.asar.english-{VERSION}.bak"


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Archive:
    def __init__(self, data):
        self.data = data
        tag, header_size, _, text_size = struct.unpack_from("<4I", data)
        self.base = 8 + header_size
        if tag != 4 or 16 + text_size > self.base or self.base > len(data):
            raise ValueError("无法读取 Antigravity 界面资源。")
        self.header = json.loads(data[16:16 + text_size])
        self.files = {}

        def index(entries, prefix=""):
            for name, entry in entries.items():
                full_name = prefix + name
                if "files" in entry:
                    index(entry["files"], full_name + "/")
                elif "offset" in entry:
                    self.files[full_name] = entry

        index(self.header["files"])

    def read(self, name):
        entry = self.files[name]
        start = self.base + int(entry["offset"])
        return self.data[start:start + entry["size"]]

    def replace(self, changes):
        chunks = []
        consumed = written = 0
        order = sorted(self.files.values(),
                       key=lambda e: (int(e["offset"]), e["size"] != 0))
        replacements = {id(self.files[name]): data for name, data in changes.items()}
        for entry in order:
            start = int(entry["offset"])
            end = start + entry["size"]
            if start < consumed or self.base + end > len(self.data):
                raise ValueError("界面资源的文件位置有误。")
            if start > consumed:
                chunks.append(self.data[self.base + consumed:self.base + start])
                written += start - consumed
            entry["offset"] = str(written)
            if id(entry) in replacements:
                content = replacements[id(entry)]
                entry["size"] = len(content)
                integrity = entry.get("integrity")
                if integrity is not None:
                    block_size = integrity["blockSize"]
                    integrity["hash"] = sha(content)
                    integrity["blocks"] = [
                        sha(content[i:i + block_size])
                        for i in range(0, len(content), block_size)
                    ] or [sha(b"")]
            else:
                content = self.data[self.base + start:self.base + end]
            chunks.append(content)
            written += len(content)
            consumed = end
        chunks.append(self.data[self.base + consumed:])
        text = json.dumps(self.header, ensure_ascii=False, separators=(",", ":")).encode()
        pad = (-len(text)) % 4
        header = struct.pack("<4I", 4, 8 + len(text) + pad, 4 + len(text) + pad, len(text))
        return b"".join((header, text, b"\0" * pad, *chunks))


def translate(original, payload):
    archive = Archive(original)
    changes = {}
    for name, edits in payload["edits"].items():
        content = archive.read(name)
        cursor = 0
        chunks = []
        for start, end, replacement in edits:
            if not cursor <= start <= end <= len(content):
                raise ValueError("汉化数据的文字位置有误。")
            chunks.extend((content[cursor:start], replacement.encode("utf-8")))
            cursor = end
        chunks.append(content[cursor:])
        changes[name] = b"".join(chunks)
    return archive.replace(changes)


def write_atomic(path, data, expected_current=None):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".antigravity-zh-",
                                         suffix=".tmp", delete=False) as handle:
            tmp = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if expected_current is not None and sha(path.read_bytes()) != expected_current:
            raise ValueError("界面文件刚刚发生变化，请退出软件后再试。")
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def desktop_is_running():
    result = subprocess.run(
        ["tasklist.exe", "/FI", "IMAGENAME eq Antigravity.exe", "/FO", "CSV", "/NH"],
        capture_output=True, check=True, timeout=10,
    )
    return any(line.lower().lstrip().startswith(b'"antigravity.exe",')
               for line in result.stdout.splitlines())


def install_roots():
    roots = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        roots.append(Path(local_app_data) / "Programs" / "antigravity")

    if os.name == "nt":
        import winreg

        uninstall = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
        registry_locations = (
            (winreg.HKEY_CURRENT_USER, 0),
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY),
        )
        for hive, view in registry_locations:
            try:
                key = winreg.OpenKey(hive, uninstall, 0, winreg.KEY_READ | view)
            except OSError:
                continue
            with key:
                index = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                    except OSError:
                        break
                    index += 1
                    try:
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if "antigravity" not in display_name.casefold():
                                continue
                            try:
                                location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                if location:
                                    roots.append(Path(location))
                            except OSError:
                                pass
                            try:
                                icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                icon = icon.strip().strip('"').rsplit(",", 1)[0].strip('"')
                                executable = Path(icon)
                                if executable.name.casefold() == "antigravity.exe":
                                    roots.append(executable.parent)
                            except (OSError, ValueError):
                                pass
                    except (OSError, TypeError, AttributeError):
                        continue

    unique = []
    seen = set()
    for root in roots:
        key = os.path.normcase(os.path.abspath(root))
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def find_install_root():
    roots = install_roots()
    installed = [root for root in roots if (root / "Antigravity.exe").is_file()
                 and (root / "resources" / "app.asar").is_file()]
    for root in installed:
        try:
            version = json.loads(Archive((root / "resources" / "app.asar").read_bytes())
                                 .read("package.json")).get("version")
        except (OSError, ValueError, KeyError, struct.error, json.JSONDecodeError):
            continue
        if version == VERSION:
            return root
    if installed:
        return installed[0]
    if roots:
        return roots[0]
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / "antigravity"


def run(action, root, fixture=False):
    resources = root / "resources"
    target = resources / "app.asar"
    backup = resources / BACKUP_NAME
    missing = []
    if not (root / "Antigravity.exe").is_file():
        missing.append("Antigravity.exe")
    if not target.is_file():
        missing.append(r"resources\app.asar")
    if missing:
        raise ValueError(
            f"找不到 Antigravity 安装文件：{', '.join(missing)}。查找位置：{root}"
        )
    with gzip.open(PAYLOAD, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload["version"] != VERSION:
        raise ValueError("补丁数据与安装程序版本不一致。")
    current = target.read_bytes()
    current_hash = sha(current)
    original_hash, chinese_hash = payload["original"], payload["chinese"]
    if current_hash not in (original_hash, chinese_hash):
        version = json.loads(Archive(current).read("package.json")).get("version", "未知")
        raise ValueError(f"当前安装是 {version}，界面文件与本补丁不匹配。请使用对应的补丁。")
    if action == "status":
        return f"Antigravity {VERSION}：{'已汉化' if current_hash == chinese_hash else '英文原版'}。"
    if action == "install" and current_hash == chinese_hash:
        return "已经安装简体中文。"
    if action == "restore" and current_hash == original_hash:
        return "已经是原来的英文界面。"
    if not fixture and desktop_is_running():
        raise ValueError("请先正常退出 Antigravity 桌面版，再运行此文件。")
    if action == "install":
        localized = translate(current, payload)
        if sha(localized) != chinese_hash:
            raise ValueError("汉化文件验证失败，原文件已保留。")
        if not backup.exists():
            write_atomic(backup, current)
        if sha(backup.read_bytes()) != original_hash:
            raise ValueError("现有的英文备份与当前版本不一致，无法安全安装。")
        write_atomic(target, localized, original_hash)
        return "简体中文已安装。现在可以打开 Antigravity。"
    if not backup.is_file():
        raise ValueError("没有找到这次安装保存的英文备份。")
    original = backup.read_bytes()
    if sha(original) != original_hash:
        raise ValueError("英文备份与当前版本不一致。")
    write_atomic(target, original, chinese_hash)
    return "英文界面已恢复。现在可以打开 Antigravity。"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("install", "restore", "status"))
    args = parser.parse_args()
    root = find_install_root()
    try:
        print(run(args.action, root))
    except (OSError, ValueError, KeyError, struct.error, subprocess.SubprocessError) as exc:
        print(f"未更改 Antigravity：{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
