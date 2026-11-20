# Antigravity 简体中文界面插件

本项目为 **Windows 版 Google Antigravity 2.34.0** 提供可本地安装的官方格式插件，包含 /localize-ui 技能、安装与恢复脚本，以及经过版本和 SHA-256 校验的中文界面补丁。

运行补丁需要 Windows 和 Python 3.8 或更新版本。

> 这是本地插件，不是 Google 插件市场中的上架项目。它通过本地脚本修改 Antigravity 的 resources/app.asar；Antigravity 插件接口本身没有替换宿主界面文案的功能。

## 安装

### 通过 Antigravity CLI 从 GitHub 安装

~~~text
agy plugin install https://github.com/Veylorni-x/antigravity-chinese-ui-plugin
~~~

### 手动安装

把仓库根目录复制到 Antigravity 全局插件目录：

~~~text
%USERPROFILE%\.gemini\config\plugins\chinese-ui-pack
~~~

重启 Antigravity 后，可从主侧栏 **Customizations → Installed** 查看插件，也可在对话中运行 /localize-ui。

## 安装汉化

确保 Antigravity 已完全退出，然后从插件页面调用 /localize-ui；也可双击：

~~~text
scripts\install-zh-cn.cmd
~~~

要恢复英文界面，退出 Antigravity 后双击：

~~~text
scripts\restore-english.cmd
~~~

## 安全与范围

- 支持版本：Windows Antigravity 2.34.0。其他版本会被拒绝，脚本不会尝试猜测兼容性。
- 安装前校验客户端版本和完整 app.asar 的 SHA-256；修改后会再次校验结果。
- 安装会在应用资源目录保留 app.asar.english-2.34.0.bak；恢复时先验证备份哈希。
- 汉化脚本只读取安装记录、app.asar 和进程列表；不连接网络、不读取聊天记录或账号凭据。
- 应用必须关闭后才能安装或恢复。脚本不会强制结束应用进程。
- Antigravity 更新后补丁可能失效；必须等到有对应新版补丁。当前脚本会安全停止，不覆盖新版本。

本项目不包含、也不分发 Google Antigravity 应用或完整 app.asar。汉化词库及部分翻译规则改编自 [Antigravity Chinese Localization](https://github.com/antigravity-cn-community/Antigravity-Chinese-Localization/tree/a22ec394f31387cab8405aebe1794a38145061d6)，原 MIT 许可见 [LICENSE.upstream](LICENSE.upstream)。
