#!/usr/bin/env python3
"""为动态表情解码帧绘制文字框、动作框和实际 alpha 外接框。"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--text-box", nargs=4, required=True, type=int)
    p.add_argument("--action-box", nargs=4, required=True, type=int)
    args = p.parse_args()

    text_box = tuple(args.text_box)
    action_box = tuple(args.action_box)
    font = ImageFont.load_default()
    frames = []
    for path in sorted(args.input_dir.glob("decoded-*.png")):
        image = Image.open(path).convert("RGBA")
        rgba = np.array(image)
        alpha = rgba[:, :, 3] >= 128
        text_mask = alpha.copy()
        text_mask[:text_box[1], :] = False
        text_mask[text_box[3]:, :] = False
        action_mask = np.zeros_like(alpha)
        action_mask[action_box[1]:action_box[3], action_box[0]:action_box[2]] = alpha[
            action_box[1]:action_box[3], action_box[0]:action_box[2]
        ]

        canvas = Image.new("RGB", image.size, "white")
        canvas.paste(image.convert("RGB"), mask=image.getchannel("A"))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle(text_box, outline="#d62728", width=3)
        draw.rectangle(action_box, outline="#1f77b4", width=3)
        if text_bbox := bbox(text_mask):
            draw.rectangle(text_bbox, outline="#ffbf00", width=3)
        if action_bbox := bbox(action_mask):
            draw.rectangle(action_bbox, outline="#2ca02c", width=3)
        draw.rectangle((8, 8, 170, 66), fill="white", outline="#555555")
        labels = [("TEXT BOX", "#d62728"), ("ACTION BOX", "#1f77b4"),
                  ("TEXT PIXELS", "#ffbf00"), ("ACTION PIXELS", "#2ca02c")]
        for i, (label, color) in enumerate(labels):
            y = 12 + i * 13
            draw.line((12, y + 4, 25, y + 4), fill=color, width=3)
            draw.text((30, y), label, fill="#111111", font=font)
        draw.text((8, 492), path.stem, fill="#111111", font=font)
        frames.append(canvas)

    if not frames:
        raise SystemExit(f"No decoded frames found in {args.input_dir}")
    cols = 2
    rows = (len(frames) + cols - 1) // cols
    contact = Image.new("RGB", (cols * 512, rows * 512), "#eeeeee")
    for i, frame in enumerate(frames):
        contact.paste(frame, ((i % cols) * 512, (i // cols) * 512))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    contact.save(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
