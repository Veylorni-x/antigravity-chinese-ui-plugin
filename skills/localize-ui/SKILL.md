---
name: localize-ui
description: Install, check, or restore the Simplified Chinese interface for Windows Antigravity 2.34.0. Use when the user asks to switch the app UI to Chinese or English.
---

# Antigravity 简体中文界面

支持 Windows 版 Antigravity 2.34.0。通过插件脚本安装、查看状态或恢复界面。

## 脚本位置

补丁脚本是本技能目录（本 SKILL.md 所在目录）下的 `scripts/patch.py`。命令的当前目录通常是用户的工作区，不是插件目录，所以必须用绝对路径调用，不能直接写 `scripts/patch.py`。

插件按默认位置安装时，PowerShell 中的完整路径为：

    $env:USERPROFILE\.gemini\config\plugins\chinese-ui-pack\skills\localize-ui\scripts\patch.py

如果该路径不存在，就用本 SKILL.md 的实际所在目录拼出路径。下文用 `<patch.py>` 代指这个绝对路径。没有 `python` 命令时可改用 `py -3`。

## 查看状态

    python -X utf8 "<patch.py>" status

## 安装中文界面

先运行：

    python -X utf8 "<patch.py>" install

如果脚本提示 Antigravity 仍在运行，不要结束它的进程。告诉用户保存工作并退出 Antigravity，然后让用户双击插件根目录中的 `scripts\install-zh-cn.cmd`。

## 恢复英文界面

先运行：

    python -X utf8 "<patch.py>" restore

如果脚本提示 Antigravity 仍在运行，不要结束它的进程。告诉用户保存工作并退出 Antigravity，然后让用户双击插件根目录中的 `scripts\restore-english.cmd`。

## 结果

只报告脚本实际返回的安装状态。脚本会校验客户端版本和原始界面文件；如果版本不匹配，会停止且保留文件不变。安装成功后，用户重新启动 Antigravity 即可看到变更。
