# 微信静态表情 Skill

本目录可单独下载和安装。仓库目录名为 `wechat-static-sticker`，原有 Skill 名称和调用方式保持为 `$wechat-sticker`。动态 Skill 位于平行目录，静态安装无需下载它。

## 安装与已有版本迁移

使用 Codex 自带的安装器时，在仓库 URL 后指定 `--name wechat-sticker`；完整命令见仓库 README。手动安装时，把本目录完整复制到宿主的技能目录，并将安装后的文件夹命名为 `wechat-sticker`。保留 `SKILL.md`、`references/`、`scripts/`、`LICENSE` 和 `NOTICE.md`。

Codex 默认个人技能目录为 `~/.codex/skills/`；使用自定义 CODEX_HOME 时，以其 `skills/` 目录为准。安装后从下一轮请求调用该技能。

已有 `wechat-sticker` 的用户无需改调用名；安装器遇到同名目录会停止，不会自动升级。更新前将旧目录完整备份到技能扫描目录之外，再安装新版，按需合并自己的定制内容。若装过过渡版 `wechat-static-sticker`，同样先备份并移出扫描目录，再以 `wechat-sticker` 安装，避免两个副本同时触发。仅更新 GitHub 仓库不会自动修改本机已安装技能。

## 开始使用

宿主需要图片生成/编辑能力和本地 Python 执行能力。附上参考图后输入：

```text
使用 $wechat-sticker，根据这张参考图制作12张微信静态表情。
保持角色特征和画风，先确认表情文案，再生成、分切并检查投稿素材。
```

技能工作流见 [SKILL.md](SKILL.md)。参考图和任务输出保存在自己的任务目录；本包提供处理脚本，不内置生成模型。

## 脚本使用

以下命令从安装后的本 Skill 目录执行，需要 Python 3.10+：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
.venv/bin/python scripts/extract_sticker_sheet.py --help
.venv/bin/python scripts/package_sticker_pack.py --help
.venv/bin/python scripts/export_wechat.py --help
```

在 Windows 使用 `.venv\Scripts\python.exe` 替代 `.venv/bin/python`。已有满足依赖的 Python 环境可以直接使用。

准备好生成的3×2静态母版后：

```bash
.venv/bin/python scripts/extract_sticker_sheet.py --input-image /path/to/sheet.png --output-dir /path/to/new-split --rows 2 --cols 3
```

按 [清单说明](references/export-manifest.md) 编写 JSON，准备全部主图及配套图后：

```bash
.venv/bin/python scripts/export_wechat.py --manifest /path/to/manifest.json --output /path/to/new-delivery
```

替换示例路径；输出目录必须尚不存在。`album` 模式需要8～24张主图及封面、图标、横幅；局部素材使用 `assets` 模式。成功后获得导出图片、`checks.json`、`submission.json`、状态说明和 `upload.zip`。检查最终图的文字、透明边缘和小尺寸效果。

导出命令、参数和处理逻辑沿用目录重构前版本；可继续使用 `python3 <skill-root>/scripts/export_wechat.py ...`。本导出器仅支持静态图片，遇到动态 GIF 会明确拒绝。
