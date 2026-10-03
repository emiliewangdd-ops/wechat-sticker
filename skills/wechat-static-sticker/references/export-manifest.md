# 导出清单
所有 path 可为绝对路径，或相对于 JSON 文件。输出目录必须未存在。每个非 main 角色最多一张。

```json
{
  "mode": "album",
  "album_name": "大耳打工猫",
  "album_intro": "大耳朵猫的打工日常",
  "artist_name": "亚比工作室",
  "copyright": "亚比工作室",
  "assets": [
    {"role": "main", "path": "stickers/01.png", "meaning": "打卡"},
    {"role": "cover", "path": "cover.png"},
    {"role": "icon", "path": "head.png"},
    {"role": "banner", "path": "banner.jpg"}
  ]
}
```
该片段仅展示字段；album 实际需要8～24张 main，含义词各不相同。assets 模式允许局部图片导出，不检查专辑齐套。角色和尺寸见 wechat-specs.md。

main/cover/icon/character_avatar/character_icon 输入需透明；封面和头像须先完成无白描边设计。其余输入需不透明且长宽比距目标不超过3%，否则先用图片工具重新排版，不强行拉伸。支持静态导出，动画输入会明确拒绝，不丢帧。

例：赞赏单独导出
```json
{"mode":"assets","assets":[
 {"role":"tip_guide","path":"guide.png"},
 {"role":"tip_thanks","path":"thanks.png"}
]}
```
后台体积提示不同：资产可加入 `max_bytes` 及非空 `limit_source` 记录实证，例如“用户提供当前后台截图，2026-09-26”。不要为通过校验虚构来源或提高阈值。

脚本只做技术检查，支持名称、介绍、artist_intro、character_intro等文字字段。版权字段不自动填写，调用方按本用户确认值提供。输出ZIP不含源照片/路径，压缩报告写入checks.json。原图保留于任务工作目录，最终文件必须实际视觉检查。若输出体积不达标，命令失败并不创建输出目录；适配后换新目录重试。
