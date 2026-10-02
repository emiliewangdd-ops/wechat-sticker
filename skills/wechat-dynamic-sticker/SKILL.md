---
name: wechat-dynamic-sticker
description: 制作、检查和整理微信动态 GIF 表情及投稿材料。用户要求动态表情、GIF 表情、帧动画、动态专辑或动态表情上传包时使用。
---

# 微信动态表情

这个 Skill 专门处理微信动态表情。静态 PNG/JPG 表情继续使用仓库根目录的 `SKILL.md`；不要因为用户只说“微信表情”就把静态和动态流程混用。

## 工作范围

- 生成或修改角色动作源和文字母版；
- 用任务目录的锁定基线构建 GIF；
- 解码复核帧数、时长、循环、透明度和 disposal；
- 输出带编号的主图、缩略图、封面、图标、横幅和投稿清单；
- 区分技术检查通过、用户视觉批准和平台审核通过。

## 规则来源

按以下顺序读取规则：

1. 本文件和 `references/dynamic-specs.md`；
2. 任务目录中的 `SOP.md`；
3. `configs/baseline.json`；
4. 微信后台当次页面提示。

任务 SOP 和锁定基线优先于通用默认值。不能为了通过一次构建而临时改基线、改帧时长、改动作框或放宽透明边缘检查。

## 构建要求

每张动态表情必须：

- 使用 512×512 RGBA 工作画布；
- 统一顶部文字区和动作框；
- 使用四帧或任务 SOP 明确的完整帧序列；
- 帧时长、循环播放、透明索引和 disposal 由基线统一控制；
- 四帧使用同一动作缩放比例和锚点；
- 通过解码后的 alpha、文字像素、边界、帧数和体积检查；
- 技术通过后仍需人工查看 GIF、解码帧和联系页。

正式构建入口：

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

构建脚本通过只表示技术检查通过。用户确认后，才把报告中的 `visual_approval` 改为 `approved_by_user`。最终 ZIP 只读取 `DELIVERY_MANIFEST.json`，不要把源照片、母版、临时帧或未批准 GIF 放入上传包。

平台规格可能变化。主图数量、尺寸、体积、缩略图和配套素材要求必须以微信后台当次提示为准；本 Skill 不代表微信平台审核通过，也不代替版权、肖像权或 AI 生成说明。

## 与静态 Skill 的关系

两个 Skill 可以共享角色资料、版权说明和通用投稿文案规则，但动态帧检查、GIF 编码和动作 SOP 只由本 Skill 负责。若同一任务同时包含静态和动态专辑，分别建立 manifest 和上传包。
