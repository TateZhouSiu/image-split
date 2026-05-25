#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

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
    chars = []
    for ch in name.lower().replace(" ", "_"):
        if ch.isalnum() or ch in ("_", "-"):
            chars.append(ch)
    return "".join(chars) or "asset"


def scale_points(points: list[Any], scale: int) -> list[Any]:
    if not points:
        return points
    if isinstance(points[0], (int, float)):
        return [round(float(v) * scale) for v in points]
    return [[round(float(v) * scale) for v in pair] for pair in points]


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


def draw_dashed_arc(
    draw: ImageDraw.ImageDraw,
    box: list[float],
    start: float,
    end: float,
    fill,
    width: int,
    dash_degrees: float,
    gap_degrees: float,
) -> None:
    angle = start
    while angle < end:
        segment_end = min(end, angle + dash_degrees)
        draw.arc(box, start=angle, end=segment_end, fill=fill, width=width)
        angle += dash_degrees + gap_degrees


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


def draw_item(draw: ImageDraw.ImageDraw, item: dict[str, Any], scale: int) -> None:
    shape = item["shape"]
    fill = parse_color(item.get("fill"), None)
    outline = parse_color(item.get("outline"), None)
    if fill is None and outline is None:
        fill = parse_color(item.get("color", "#0052AA"))
    width = max(1, int(round(float(item.get("width", 2)) * scale)))
    if shape == "line":
        draw.line(scale_points(item["points"], scale), fill=fill or outline, width=width)
    elif shape == "dashed_line":
        x0, y0, x1, y1 = scale_points(item["points"], scale)
        draw_dashed_line(
            draw,
            (x0, y0),
            (x1, y1),
            fill or outline,
            width,
            int(item.get("dash", 8)) * scale,
            int(item.get("gap", 8)) * scale,
        )
    elif shape == "rect":
        draw.rectangle(scale_points(item["box"], scale), fill=fill, outline=outline, width=width)
    elif shape == "rounded_rect":
        draw.rounded_rectangle(
            scale_points(item["box"], scale),
            radius=int(round(float(item.get("radius", 8)) * scale)),
            fill=fill,
            outline=outline,
            width=width,
        )
    elif shape == "ellipse":
        draw.ellipse(scale_points(item["box"], scale), fill=fill, outline=outline, width=width)
    elif shape == "circle":
        cx, cy = item["center"]
        r = float(item["radius"])
        draw.ellipse(
            [round((cx - r) * scale), round((cy - r) * scale), round((cx + r) * scale), round((cy + r) * scale)],
            fill=fill,
            outline=outline,
            width=width,
        )
    elif shape == "polygon":
        draw.polygon(scale_points(item["points"], scale), fill=fill, outline=outline)
    elif shape == "arc":
        draw.arc(
            scale_points(item["box"], scale),
            start=float(item.get("start", 0)),
            end=float(item.get("end", 360)),
            fill=fill or outline,
            width=width,
        )
    elif shape == "dashed_arc":
        draw_dashed_arc(
            draw,
            scale_points(item["box"], scale),
            float(item.get("start", 0)),
            float(item.get("end", 360)),
            fill or outline,
            width,
            float(item.get("dash", 8)),
            float(item.get("gap", 8)),
        )
    elif shape == "arrow":
        draw_arrow(
            draw,
            scale_points(item["from"], scale),
            scale_points(item["to"], scale),
            fill or outline,
            int(item.get("width", 16)) * scale,
            int(item.get("head", 24)) * scale,
        )
    else:
        raise ValueError(f"Unsupported shape: {shape}")


def render_draw_asset(asset: dict[str, Any]) -> Image.Image:
    x, y, w, h = [int(v) for v in asset["position"]]
    scale = int(asset.get("scale", 4))
    canvas = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for item in asset.get("items", []):
        draw_item(draw, item, scale)
    return canvas.resize((w, h), Image.Resampling.LANCZOS)


def alpha_from_background(img: Image.Image, bg: tuple[int, int, int], threshold: float, soft: float) -> Image.Image:
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    dist = np.sqrt(((arr - np.asarray(bg, dtype=np.float32)) ** 2).sum(axis=2))
    if soft <= 0:
        alpha = (dist > threshold).astype(np.uint8) * 255
    else:
        alpha = np.clip((dist - threshold) / soft * 255, 0, 255).astype(np.uint8)
    rgba = np.dstack([arr.astype(np.uint8), alpha])
    return Image.fromarray(rgba, "RGBA")


def alpha_from_lightness(img: Image.Image, threshold: float, soft: float) -> Image.Image:
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    alpha = np.clip((lum - threshold) / max(soft, 1) * 255, 0, 255)
    dark_blue_bg = (
        (arr[:, :, 2] > arr[:, :, 0] + 25)
        & (arr[:, :, 2] > arr[:, :, 1] - 5)
        & (lum < threshold + 8)
    )
    alpha[dark_blue_bg] = 0
    rgba = np.dstack([arr.astype(np.uint8), alpha.astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def alpha_from_color_distance(img: Image.Image, color: tuple[int, int, int], threshold: float, soft: float) -> Image.Image:
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    dist = np.sqrt(((arr - np.asarray(color, dtype=np.float32)) ** 2).sum(axis=2))
    alpha = np.clip((threshold + max(soft, 1) - dist) / max(soft, 1) * 255, 0, 255)
    rgba = np.dstack([arr.astype(np.uint8), alpha.astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def trim_transparent(img: Image.Image, padding: int = 0) -> tuple[Image.Image, tuple[int, int, int, int]]:
    rgba = img.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if not bbox:
        return rgba, (0, 0, rgba.size[0], rgba.size[1])
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(rgba.size[0], bbox[2] + padding)
    bottom = min(rgba.size[1], bbox[3] + padding)
    return rgba.crop((left, top, right, bottom)), (left, top, right, bottom)


def render_crop_asset(asset: dict[str, Any], source: Image.Image, root: Path, bg: tuple[int, int, int]) -> Image.Image:
    source_file = asset.get("sourceFile")
    src = Image.open(root / source_file).convert("RGBA") if source_file else source.convert("RGBA")
    x, y, w, h = [int(v) for v in asset["position"]]
    crop = src.crop((x, y, x + w, y + h))
    if asset.get("mask") == "nonwhite":
        crop = alpha_from_background(
            crop,
            tuple(asset.get("backgroundRgb", bg)),
            float(asset.get("threshold", 28)),
            float(asset.get("soft", 18)),
        )
    elif asset.get("mask") == "light":
        crop = alpha_from_lightness(
            crop,
            float(asset.get("threshold", 135)),
            float(asset.get("soft", 35)),
        )
    elif asset.get("mask") == "color":
        color = parse_color(asset.get("color", "#004EA2"), (0, 78, 162, 255))
        crop = alpha_from_color_distance(
            crop,
            color[:3],
            float(asset.get("threshold", 55)),
            float(asset.get("soft", 24)),
        )
    elif asset.get("mask") == "alpha":
        crop = crop.convert("RGBA")
    else:
        crop = crop.convert("RGBA")
        if "alpha" in asset:
            crop.putalpha(int(asset["alpha"]))
    if asset.get("clipEllipse"):
        mask = Image.new("L", crop.size, 0)
        draw = ImageDraw.Draw(mask)
        inset = int(asset.get("ellipseInset", 0))
        draw.ellipse([inset, inset, crop.size[0] - 1 - inset, crop.size[1] - 1 - inset], fill=255)
        alpha = crop.getchannel("A")
        crop.putalpha(Image.fromarray(np.minimum(np.asarray(alpha), np.asarray(mask)).astype(np.uint8), "L"))
    if asset.get("erase"):
        draw = ImageDraw.Draw(crop)
        for rect in asset["erase"]:
            box = rect["box"]
            fill_value = str(rect.get("fill", "#F7F8F7")).strip().lower()
            fill = (0, 0, 0, 0) if fill_value == "transparent" else parse_color(rect.get("fill", "#F7F8F7"), (247, 248, 247, 255))
            draw.rectangle(box, fill=fill)
    if asset.get("trim"):
        trimmed, (left, top, right, bottom) = trim_transparent(crop, int(asset.get("trimPadding", 0)))
        if asset.get("trimMode") == "resize-canvas":
            crop = Image.new("RGBA", crop.size, (0, 0, 0, 0))
            crop.alpha_composite(trimmed, (left, top))
        else:
            crop = trimmed
    return crop


def make_contact_sheet(out_dir: Path, records: list[dict[str, Any]]) -> None:
    thumb_w, thumb_h, label_h = 220, 140, 40
    cols = 4
    rows = max(1, math.ceil(len(records) / cols))
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (238, 240, 243))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    checker = Image.new("RGB", (thumb_w, thumb_h), (248, 248, 248))
    cdraw = ImageDraw.Draw(checker)
    for yy in range(0, thumb_h, 12):
        for xx in range(0, thumb_w, 12):
            if (xx // 12 + yy // 12) % 2 == 0:
                cdraw.rectangle([xx, yy, xx + 11, yy + 11], fill=(226, 229, 233))
    for idx, item in enumerate(records):
        img = Image.open(out_dir / item["file"]).convert("RGBA")
        tile = Image.new("RGB", (thumb_w, thumb_h + label_h), "white")
        bg = checker.copy()
        img.thumbnail((thumb_w - 10, thumb_h - 10), Image.Resampling.LANCZOS)
        bg.paste(img, ((thumb_w - img.width) // 2, (thumb_h - img.height) // 2), img)
        tile.paste(bg, (0, 0))
        draw = ImageDraw.Draw(tile)
        draw.text((6, thumb_h + 4), item["name"][:32], fill=(0, 70, 145), font=font)
        draw.text((6, thumb_h + 21), f"{item['position'][2]}x{item['position'][3]}", fill=(92, 97, 105), font=font)
        sheet.paste(tile, ((idx % cols) * thumb_w, (idx // cols) * (thumb_h + label_h)))
    sheet.save(out_dir / "assets_contact_sheet.png")


def make_composite(out_dir: Path, records: list[dict[str, Any]], size: tuple[int, int], background: tuple[int, int, int, int]) -> None:
    composite = Image.new("RGBA", size, background)
    for record in records:
        img = Image.open(out_dir / record["file"]).convert("RGBA")
        x, y, _, _ = record["position"]
        composite.alpha_composite(img, (int(x), int(y)))
    composite.convert("RGB").save(out_dir / "composite_no_text_preview.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a slide into cropped atomic visual assets with placement metadata.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--elements", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    source = Image.open(args.image).convert("RGB")
    spec = json.loads(args.elements.read_text("utf-8"))
    canvas = tuple(spec.get("canvas", source.size))
    if tuple(source.size) != canvas:
        raise ValueError(f"Source size {source.size} does not match spec canvas {canvas}")
    bg = parse_color(spec.get("background", "#F7F8F7"), (247, 248, 247, 255))
    bg_rgb = bg[:3] if bg else (247, 248, 247)
    records: list[dict[str, Any]] = []
    for idx, asset in enumerate(spec.get("assets", []), 1):
        name = safe_name(str(asset["name"]))
        file_name = f"{idx:02d}_{name}.png"
        if asset["type"] == "draw":
            img = render_draw_asset(asset)
        elif asset["type"] == "crop":
            img = render_crop_asset(asset, source, args.elements.parent, bg_rgb)
        else:
            raise ValueError(f"Unsupported asset type: {asset['type']}")
        img.save(args.out / file_name)
        record = {
            "file": file_name,
            "name": name,
            "type": asset["type"],
            "kind": asset.get("kind", asset["type"]),
            "placement": "crop",
            "position": [int(v) for v in asset["position"]],
            "canvas": list(canvas),
            "slideSize": spec.get("slideSize", [960, 540]),
            "atomic": bool(asset.get("atomic", True)),
        }
        if asset.get("notes"):
            record["notes"] = asset["notes"]
        records.append(record)
    make_contact_sheet(args.out, records)
    make_composite(args.out, records, canvas, bg or (247, 248, 247, 255))
    (args.out / "manifest.json").write_text(json.dumps({
        "source": str(args.image),
        "elements": str(args.elements),
        "route": "atomic-assets",
        "canvas": list(canvas),
        "slideSize": spec.get("slideSize", [960, 540]),
        "asset_count": len(records),
        "assets": records,
    }, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({"out": str(args.out), "assets": len(records)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
