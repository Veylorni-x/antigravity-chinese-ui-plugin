---
name: localize-ui
description: Install, check, or restore the Simplified Chinese interface for Windows Antigravity 2.34.0. Use when the user asks to switch the app UI to Chinese or English.
---

# Antigravity 简体中文界面

支持 Windows 版 Antigravity 2.34.0。通过插件脚本安装、查看状态或恢复界面。

## 查看状态

运行命令：

    python -X utf8 scripts/patch.py status

## 安装中文界面

先运行：

    python -X utf8 scripts/patch.py install

如果脚本提示 Antigravity 仍在运行，不要结束它的进程。告诉用户保存工作并退出 Antigravity，然后让用户双击插件安装目录中的 scripts/install-zh-cn.cmd。

## 恢复英文界面

先运行：

    python -X utf8 scripts/patch.py restore

如果脚本提示 Antigravity 仍在运行，不要结束它的进程。告诉用户保存工作并退出 Antigravity，然后让用户双击插件安装目录中的 scripts/restore-english.cmd。

## 结果

只报告脚本实际返回的安装状态。脚本会校验客户端版本和原始界面文件；如果版本不匹配，会停止且保留文件不变。安装成功后，用户重新启动 Antigravity 即可看到变更。
