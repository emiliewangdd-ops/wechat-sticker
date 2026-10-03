---
name: wechat-dynamic-sticker
description: 从参考图和表情需求制作、检查并整理微信动态 GIF 表情及投稿材料；适用于动态表情、GIF 表情、帧动画、动态专辑或动态表情上传包。已有动作帧时也可只执行构建与质检。
---

# 微信动态表情

这个 Skill 覆盖“参考图/需求 → 角色与风格基线 → 动作源 → 512px 工作 GIF → 240px 投稿素材 → 人工审核”的完整链路。静态 PNG/JPG 表情继续使用仓库根目录的 `SKILL.md`；不要因为用户只说“微信表情”就把静态和动态流程混用。

不要把本 Skill 当成“只运行一个 GIF 脚本”。构建器不能凭空发明角色身份、动作含义或字形风格；如果输入只有一句话和一张参考图，先执行[创作流程](references/creation-workflow.md)，生成并审核文字母版和四帧动作源，再进入构建阶段。

## 工作范围

- 生成或修改角色动作源和文字母版；
- 用任务目录的锁定基线构建 GIF；
- 解码复核帧数、时长、循环、透明度和 disposal；
- 输出带编号的主图、缩略图、封面、图标、横幅和投稿清单；
- 区分技术检查通过、用户视觉批准和平台审核通过。

## 规则来源

按以下顺序读取规则：

1. 微信后台当次页面提示；
2. 本文件和 `references/dynamic-specs.md`；
3. 任务目录中的 `SOP.md`；
4. `configs/baseline.json`。

任务 SOP 和锁定基线优先于通用默认值。不能为了通过一次构建而临时改基线、改帧时长、改动作框或放宽透明边缘检查。

## 端到端流程

1. 收集参考图、角色身份特征、表情文字、动作含义和投稿数量；没有参考图时不得臆造用户想要的特定角色。
2. 读取[创作流程](references/creation-workflow.md)，建立任务目录、角色/画风/字形基线和四帧动作分镜。
3. 生成动作源和文字母版。四帧必须表达同一个动作语义，不能只做抖动、缩放或换字；先人工确认素材，再写入 locked baseline。
4. 使用任务配置运行 512×512 工作画布构建器，并查看解码帧、联系页和报告。
5. 通过技术和视觉审核后，使用仓库根目录的 `scripts/export_wechat.py` 将批准的 GIF 导出为 240×240 主图、120×120 缩略图、封面、图标和横幅。工作 GIF 不是最终上传文件。
6. 只把 `DELIVERY_MANIFEST.json` 白名单中的文件打包；输出状态必须明确写成 `ready_for_upload`，不得声称已经通过微信平台审核。

如果用户要求“复现某个已有成品”，必须把该成品作为视觉参考，提取可复用的角色、字形、版式、动作节奏和透明边缘约束；不能只读取 GIF 的技术参数就宣称风格可复现。

## 构建要求

每张动态表情必须：

- 使用 512×512 RGBA 工作画布；
- 统一顶部文字区和动作框；
- 使用四帧或任务 SOP 明确的完整帧序列；
- 帧时长、循环播放、透明索引和 disposal 由基线统一控制；
- 四帧使用同一动作缩放比例和锚点；
- 通过解码后的 alpha、文字像素、边界、帧数和体积检查；
- 技术通过后仍需人工查看 GIF、解码帧和联系页。

正式上传前另须满足：主图为投稿页面要求的最终尺寸（默认 240×240）、缩略图和配套素材齐全、主图与缩略图一一对应，并通过最终 ZIP 内容检查。

正式构建入口（用于 512px 工作 GIF）：

```bash
python3 <skill-root>/scripts/build_dynamic_sticker.py <task>/configs/<sticker>.json
```

生成标注检查图：

```bash
python3 <skill-root>/scripts/annotate_dynamic_frames.py \
  --input-dir <task>/checks/<sticker> \
  --output <task>/checks/<sticker>/annotated-contact.png \
  --text-box 0 0 512 104 \
  --action-box 0 104 512 512
```

## 审批和交付

构建脚本通过只表示技术检查通过。用户确认后，才把报告中的 `visual_approval` 改为 `approved_by_user`。最终 ZIP 只读取 `DELIVERY_MANIFEST.json`，不要把源照片、母版、临时帧、512px 工作 GIF 或未批准 GIF 放入上传包。

最终素材导出使用仓库根目录的导出器：

```bash
python3 <repo-root>/scripts/export_wechat.py \
  --manifest <task>/delivery/manifest.json \
  --output <new-output-dir>
```

动态专辑 manifest 至少要列出每张已批准主图、唯一含义词、对应缩略图帧，以及封面、聊天图标和横幅；导出器会拒绝静态混入、尺寸不符、透明度错误、含义词重复和旧输出目录覆盖。

平台规格可能变化。主图数量、尺寸、体积、缩略图和配套素材要求必须以微信后台当次提示为准；本 Skill 不代表微信平台审核通过，也不代替版权、肖像权或 AI 生成说明。

## 与静态 Skill 的关系

两个 Skill 可以共享角色资料、版权说明和通用投稿文案规则，但动态帧检查、GIF 编码和动作 SOP 只由本 Skill 负责。若同一任务同时包含静态和动态专辑，分别建立 manifest 和上传包。
