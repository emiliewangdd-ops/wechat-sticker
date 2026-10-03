# Changelog

## Unreleased

- 恢复静态 Skill 原调用名 `wechat-sticker` 和 Skill 内相对导出命令；目录仍为 `skills/wechat-static-sticker/`。
- 静态目录补齐与重构前一致的导出器及 MIT 许可证、安装使用说明；根目录保留原静态导出器兼容副本。
- 恢复范围仅限静态 Skill；动态导出链路尚待修复。
- 将静态与动态微信表情 Skill 整理为 `skills/wechat-static-sticker/` 与 `skills/wechat-dynamic-sticker/` 两个平行目录。
- 更新 README、NOTICE、安装说明和导出器中的静态 Skill 路径。
- 补充微信动态表情从参考图、动作分镜、文字基线到最终投稿导出的完整流程。
- 明确区分 512×512 工作 GIF 与 240×240 最终上传素材，补充视觉审核和投稿包边界。
- 新增动态表情创作流程参考，避免只依赖已有动作帧和锁定配置。

## 0.1.0

- 基于 MemeSticker 增加微信表情专辑投稿清单。
- 增加主图、封面、聊天图标、横幅、角色和艺术家资料的尺寸与体积检查。
- 增加中文含义词、专辑文案和投稿 ZIP 导出。
- 保留上游 MIT License、版权声明及核心分切脚本。
