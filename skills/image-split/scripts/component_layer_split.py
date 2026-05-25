#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def parse_color(value: str | None, default: tuple[int, int, int, int] | None = None) -> tuple[int, int, int, int] | None:
    if value is None:
        return default
    s = value.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) == 6:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
    if len(s) == 8:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16))
    raise ValueError(f"Unsupported color: {value}")


def safe_name(name: str) -> str:
    out = []
    for ch in name.lower().replace(" ", "_"):
        if ch.isalnum() or ch in ("_", "-"):
            out.append(ch)
    return "".join(out) or "layer"


def load_ocr_boxes(path: Path | None, slide: int | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = json.loads(path.read_text("utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "slides" in data:
        for record in data["slides"]:
            if slide is None or int(record.get("slide", -1)) == slide:
                return record.get("text_boxes", [])
    if isinstance(data, dict) and "text_boxes" in data:
        return data["text_boxes"]
    return []


def text_mask_from_ocr(
    boxes: list[dict[str, Any]],
    image_size: tuple[int, int],
    ocr_size: tuple[int, int],
    pad: int,
) -> np.ndarray:
    width, height = image_size
    ocr_w, ocr_h = ocr_size
    sx = width / ocr_w
    sy = height / ocr_h
    mask = np.zeros((height, width), dtype=np.uint8)
    for item in boxes:
        text = str(item.get("text", "")).strip()
        bbox = item.get("bbox")
        if not text or not isinstance(bbox, list) or len(bbox) != 4:
            continue
        x, y, bw, bh = [float(v) for v in bbox]
        local_pad = max(2, pad if len(text) > 2 else pad // 2)
        x0 = max(0, int(x * sx) - local_pad)
        y0 = max(0, int(y * sy) - local_pad)
        x1 = min(width, int((x + bw) * sx) + local_pad)
        y1 = min(height, int((y + bh) * sy) + local_pad)
        if x1 > x0 and y1 > y0:
            mask[y0:y1, x0:x1] = 255
    if (mask > 0).any():
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)
    return mask


def foreground_mask(rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    blueish = (b > r + 6) & (b > g - 8) & (sat > 8) & (val > 40)
    colorful = (sat > 22) & (val > 50)
    dark = gray < 218
    pale_blue = (b > r + 4) & (b >= g - 3) & (gray < 244) & (sat > 4)
    mask = (blueish | colorful | dark | pale_blue).astype(np.uint8) * 255
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))


def lineart_mask(rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    sat = hsv[:, :, 1]
    blue_pale = (b > r + 3) & (b >= g - 3) & (gray < 245) & (sat > 3)
    edges = cv2.Canny(gray, 24, 70)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1) > 0
    stronger = (gray < 225) & (sat > 8)
    return ((blue_pale & (edges | stronger))).astype(np.uint8) * 255


def region_mask(shape: tuple[int, int], regions: list[list[int]]) -> np.ndarray:
    height, width = shape
    mask = np.zeros((height, width), dtype=np.uint8)
    for region in regions:
        if len(region) != 4:
            raise ValueError(f"Region must be [x0,y0,x1,y1], got {region}")
        x0, y0, x1, y1 = [int(v) for v in region]
        mask[max(0, y0):min(height, y1), max(0, x0):min(width, x1)] = 255
    return mask


def draw_dashed_line(draw: ImageDraw.ImageDraw, p0: tuple[float, float], p1: tuple[float, float], fill, width: int, dash: int, gap: int) -> None:
    x0, y0 = p0
    x1, y1 = p1
    length = math.hypot(x1 - x0, y1 - y0)
    if length <= 0:
        return
    dx = (x1 - x0) / length
    dy = (y1 - y0) / length
    pos = 0.0
    while pos < length:
        end = min(length, pos + dash)
        draw.line([(x0 + dx * pos, y0 + dy * pos), (x0 + dx * end, y0 + dy * end)], fill=fill, width=width)
        pos += dash + gap


def draw_arrow(draw: ImageDraw.ImageDraw, start: list[float], end: list[float], fill, width: int, head: int) -> None:
    x0, y0 = start
    x1, y1 = end
    if abs(y1 - y0) <= abs(x1 - x0):
        direction = 1 if x1 >= x0 else -1
        body_end = x1 - direction * head
        draw.line([(x0, y0), (body_end, y0)], fill=fill, width=width)
        draw.polygon([(body_end, y0 - head), (x1, y0), (body_end, y0 + head)], fill=fill)
    else:
        direction = 1 if y1 >= y0 else -1
        body_end = y1 - direction * head
        draw.line([(x0, y0), (x0, body_end)], fill=fill, width=width)
        draw.polygon([(x0 - head, body_end), (x0, y1), (x0 + head, body_end)], fill=fill)


def draw_item(draw: ImageDraw.ImageDraw, item: dict[str, Any]) -> None:
    shape = item["shape"]
    fill = parse_color(item.get("fill"), None)
    outline = parse_color(item.get("outline"), None)
    if fill is None and outline is None:
        fill = parse_color(item.get("color", "#0052AA"))
    width = int(item.get("width", 2))
    if shape == "line":
        draw.line(item["points"], fill=fill or outline, width=width)
    elif shape == "dashed_line":
        x0, y0, x1, y1 = item["points"]
        draw_dashed_line(draw, (x0, y0), (x1, y1), fill or outline, width, int(item.get("dash", 8)), int(item.get("gap", 8)))
    elif shape == "rect":
        draw.rectangle(item["box"], fill=fill, outline=outline, width=width)
    elif shape == "rounded_rect":
        draw.rounded_rectangle(item["box"], radius=int(item.get("radius", 8)), fill=fill, outline=outline, width=width)
    elif shape == "ellipse":
        draw.ellipse(item["box"], fill=fill, outline=outline, width=width)
    elif shape == "circle":
        cx, cy = item["center"]
        r = float(item["radius"])
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)
    elif shape == "polygon":
        draw.polygon(item["points"], fill=fill, outline=outline)
    elif shape == "arrow":
        draw_arrow(draw, item["from"], item["to"], fill or outline, int(item.get("width", 16)), int(item.get("head", 24)))
    elif shape == "dashed_rounded_rect":
        x0, y0, x1, y1 = item["box"]
        radius = int(item.get("radius", 12))
        color = outline or fill
        dash = int(item.get("dash", 8))
        gap = int(item.get("gap", 8))
        draw_dashed_line(draw, (x0 + radius, y0), (x1 - radius, y0), color, width, dash, gap)
        draw_dashed_line(draw, (x0 + radius, y1), (x1 - radius, y1), color, width, dash, gap)
        draw_dashed_line(draw, (x0, y0 + radius), (x0, y1 - radius), color, width, dash, gap)
        draw_dashed_line(draw, (x1, y0 + radius), (x1, y1 - radius), color, width, dash, gap)
        draw.arc([x0, y0, x0 + radius * 2, y0 + radius * 2], 180, 270, fill=color, width=width)
        draw.arc([x1 - radius * 2, y0, x1, y0 + radius * 2], 270, 360, fill=color, width=width)
        draw.arc([x1 - radius * 2, y1 - radius * 2, x1, y1], 0, 90, fill=color, width=width)
        draw.arc([x0, y1 - radius * 2, x0 + radius * 2, y1], 90, 180, fill=color, width=width)
    else:
        raise ValueError(f"Unsupported shape: {shape}")


def bbox_from_alpha(alpha: np.ndarray) -> list[int]:
    ys, xs = np.where(alpha > 0)
    if xs.size == 0:
        return [0, 0, 0, 0]
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def save_rgba(path: Path, rgb: np.ndarray, alpha: np.ndarray, blur_alpha: bool) -> list[int]:
    if blur_alpha and (alpha > 0).any():
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
    rgba = np.dstack([rgb, alpha.astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(path)
    return bbox_from_alpha(alpha)


def build_draw_layer(layer: dict[str, Any], size: tuple[int, int], out_path: Path) -> list[int]:
    width, height = size
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for item in layer.get("items", []):
        draw_item(draw, item)
    canvas.save(out_path)
    return bbox_from_alpha(np.asarray(canvas)[:, :, 3])


def build_extract_layer(layer: dict[str, Any], rgb: np.ndarray, text_mask: np.ndarray, out_path: Path) -> list[int]:
    height, width = rgb.shape[:2]
    regions = layer.get("regions", [[0, 0, width, height]])
    base = str(layer.get("mask", "foreground"))
    if base == "foreground":
        mask = foreground_mask(rgb)
    elif base == "lineart":
        mask = lineart_mask(rgb)
    elif base == "region":
        mask = np.full((height, width), 255, dtype=np.uint8)
    else:
        raise ValueError(f"Unsupported extract mask: {base}")
    mask = cv2.bitwise_and(mask, region_mask((height, width), regions))
    if bool(layer.get("subtract_text", False)) and text_mask.size:
        mask[text_mask > 0] = 0
    close = int(layer.get("close", 0))
    if close > 1:
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    dilate = int(layer.get("dilate", 0))
    if dilate > 0:
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=dilate)
    return save_rgba(out_path, rgb, mask, bool(layer.get("blur_alpha", True)))


def make_contact_sheet(out_dir: Path, manifest: list[dict[str, Any]], size: tuple[int, int]) -> None:
    width, height = size
    thumb_w, thumb_h = 320, round(320 * height / width)
    label_h = 28
    cols = 2
    rows = max(1, math.ceil(len(manifest) / cols))
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (236, 238, 241))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    checker = Image.new("RGB", (thumb_w, thumb_h), (245, 245, 245))
    d0 = ImageDraw.Draw(checker)
    for y in range(0, thumb_h, 12):
        for x in range(0, thumb_w, 12):
            if (x // 12 + y // 12) % 2 == 0:
                d0.rectangle([x, y, x + 11, y + 11], fill=(225, 228, 232))
    for i, item in enumerate(manifest):
        img = Image.open(out_dir / item["file"]).convert("RGBA")
        x0, y0, x1, y1 = item["bbox"]
        crop = img.crop((x0, y0, x1, y1)) if x1 > x0 and y1 > y0 else img
        crop.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (thumb_w, thumb_h + label_h), "white")
        bg = checker.copy()
        bg.paste(crop, ((thumb_w - crop.width) // 2, (thumb_h - crop.height) // 2), crop)
        tile.paste(bg, (0, 0))
        draw = ImageDraw.Draw(tile)
        draw.text((8, thumb_h + 5), item["file"], fill=(0, 70, 145), font=font)
        sheet.paste(tile, ((i % cols) * thumb_w, (i // cols) * (thumb_h + label_h)))
    sheet.save(out_dir / "assets_contact_sheet.png")


def make_composite(out_dir: Path, manifest: list[dict[str, Any]], size: tuple[int, int], background: tuple[int, int, int, int]) -> None:
    composite = Image.new("RGBA", size, background)
    for item in manifest:
        img = Image.open(out_dir / item["file"]).convert("RGBA")
        composite.alpha_composite(img)
    composite.convert("RGB").save(out_dir / "composite_no_text_preview.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a slide image into semantic full-canvas transparent visual layers.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--recipe", required=True, type=Path)
    parser.add_argument("--ocr-json", type=Path)
    parser.add_argument("--slide", type=int)
    parser.add_argument("--ocr-width", type=int, default=960)
    parser.add_argument("--ocr-height", type=int, default=540)
    parser.add_argument("--text-pad", type=int, default=8)
    parser.add_argument("--background", default="#F7F8F7")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rgb = np.asarray(Image.open(args.image).convert("RGB"))
    height, width = rgb.shape[:2]
    recipe = json.loads(args.recipe.read_text("utf-8"))
    text_boxes = load_ocr_boxes(args.ocr_json, args.slide)
    text_mask = text_mask_from_ocr(text_boxes, (width, height), (args.ocr_width, args.ocr_height), args.text_pad)
    if args.ocr_json is not None:
        Image.fromarray(text_mask, "L").save(args.out / "text_mask_for_reference.png")

    manifest: list[dict[str, Any]] = []
    for idx, layer in enumerate(recipe.get("layers", []), 1):
        name = safe_name(str(layer.get("name", f"layer_{idx:02d}")))
        filename = f"{idx:02d}_{name}.png"
        out_path = args.out / filename
        if layer.get("type") == "draw":
            bbox = build_draw_layer(layer, (width, height), out_path)
        elif layer.get("type") == "extract":
            bbox = build_extract_layer(layer, rgb, text_mask, out_path)
        else:
            raise ValueError(f"Unsupported layer type: {layer.get('type')}")
        manifest.append({
            "file": filename,
            "name": name,
            "type": layer.get("type"),
            "bbox": bbox,
            "source": str(args.image),
            "canvas": [width, height],
        })

    bg = parse_color(args.background, (247, 248, 247, 255))
    make_composite(args.out, manifest, (width, height), bg or (247, 248, 247, 255))
    make_contact_sheet(args.out, manifest, (width, height))
    (args.out / "manifest.json").write_text(json.dumps({
        "source": str(args.image),
        "recipe": str(args.recipe),
        "slide": args.slide,
        "canvas": [width, height],
        "asset_count": len(manifest),
        "assets": manifest,
    }, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({"out": str(args.out), "assets": len(manifest)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
