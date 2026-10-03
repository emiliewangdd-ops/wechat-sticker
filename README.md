# wechat-sticker

一个面向微信表情开放平台投稿的 Agent Skills 集合。它在 `meme-sticker` 的表情生成与分切流程基础上，增加微信投稿规格检查、封面/聊天图标/横幅等配套素材清单、投稿文案和 ZIP 导出。

## 目录结构

静态和动态表情是两个平行的 Skill：

```text
skills/
├── wechat-static-sticker/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
└── wechat-dynamic-sticker/
    ├── SKILL.md
    ├── references/
    └── scripts/
scripts/
└── export_wechat.py       # 静态/动态共用的最终投稿素材导出器
```

## 来源与许可证

本项目是 [shanliuling/meme-sticker](https://github.com/shanliuling/meme-sticker) 的衍生作品。上游项目使用 MIT License；本仓库保留上游 `LICENSE` 文件及其版权声明，并在此基础上发布新增和修改内容。

MIT 允许复制、修改、发布、再许可和商业使用，但分发本项目时必须继续保留 MIT 许可文本和原作者版权声明。微信平台的审核、版权、肖像权和 AI 生成内容要求仍需由投稿者自行确认；本 Skill 不代表微信官方，也不保证审核通过。

## 使用范围

- `skills/wechat-static-sticker/`：生成 8–24 张静态微信表情，并检查 240×240 与文件大小。
- `skills/wechat-dynamic-sticker/`：从参考图、动作分镜和四帧动作源构建动态表情，再导出最终投稿素材。
- 导出封面、聊天图标、专辑横幅及可选的角色、艺术家资料和赞赏素材。
- 生成 `checks.json`、`submission.json`、投稿文案和上传 ZIP。

图片创作仍依赖宿主 Agent 的图片生成或编辑能力；本仓库只负责工作流说明、图像处理、规格校验和打包，不内置模型、API Key 或自动投稿功能。

## 安装

支持 Skill 的 Agent 应引用对应目录中的 `SKILL.md`：

```text
skills/wechat-static-sticker/SKILL.md
skills/wechat-dynamic-sticker/SKILL.md
```

运行脚本需要 Python 3.10+，并安装 `skills/wechat-static-sticker/scripts/requirements.txt` 中的 Pillow 和 NumPy。

安装动态 Skill：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/emiliewangdd-ops/wechat-sticker/tree/main/skills/wechat-dynamic-sticker
```

安装静态 Skill 时，将 URL 中的路径替换为 `skills/wechat-static-sticker`。安装后新开任务，然后显式使用 `$wechat-dynamic-sticker` 或 `$wechat-static-sticker`；也可以直接描述需求，让 Agent 自动选择。

## 与上游的关系

上游的核心分切与打包脚本保留在 `scripts/` 中；微信规格、清单字段和导出校验属于本项目新增或适配内容。若继续修改上游代码，请同步检查其 MIT 版权声明，不要把上游代码或其示例素材误写成原创。

## 免责声明

规格来自本项目维护时记录的微信官方页面截图和用户提供的审核标准，平台规则可能变化，投稿后台当次提示优先。素材是否拥有足够的著作权、肖像权和商用授权，需要投稿者自行核验。
