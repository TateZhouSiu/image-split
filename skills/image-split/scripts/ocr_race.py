#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")


def split_engines(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def run_tesseract(image: Path, lang: str, psm: int, min_conf: float) -> dict[str, Any]:
    if shutil.which("tesseract") is None:
        return {
            "engine": "tesseract",
            "status": "skipped",
            "error": "tesseract executable was not found on PATH",
            "text_boxes": [],
        }
    cmd = [
        "tesseract",
        str(image),
        "stdout",
        "-l",
        lang,
        "--psm",
        str(psm),
        "tsv",
    ]
    proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        return {
            "engine": "tesseract",
            "status": "error",
            "command": cmd,
            "stderr": proc.stderr,
            "text_boxes": [],
        }

    boxes: list[dict[str, Any]] = []
    reader = csv.DictReader(proc.stdout.splitlines(), delimiter="\t")
    for row in reader:
        text = (row.get("text") or "").strip()
        if not text:
            continue
        try:
            conf = float(row.get("conf") or -1)
            left = int(float(row.get("left") or 0))
            top = int(float(row.get("top") or 0))
            width = int(float(row.get("width") or 0))
            height = int(float(row.get("height") or 0))
        except ValueError:
            continue
        if conf < min_conf or width <= 0 or height <= 0:
            continue
        boxes.append({
            "text": text,
            "confidence": conf / 100.0,
            "bbox": [left, top, width, height],
            "level": row.get("level"),
            "block": row.get("block_num"),
            "paragraph": row.get("par_num"),
            "line": row.get("line_num"),
            "word": row.get("word_num"),
        })
    return {
        "engine": "tesseract",
        "status": "ok",
        "command": cmd,
        "language": lang,
        "psm": psm,
        "text_boxes": boxes,
        "raw_text": " ".join(item["text"] for item in boxes),
        "stderr": proc.stderr.strip(),
    }


def normalize_polygon(poly: Any) -> list[int] | None:
    if not isinstance(poly, (list, tuple)) or not poly:
        return None
    xs: list[float] = []
    ys: list[float] = []
    for point in poly:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            xs.append(float(point[0]))
            ys.append(float(point[1]))
    if not xs or not ys:
        return None
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    return [round(x0), round(y0), max(1, round(x1 - x0)), max(1, round(y1 - y0))]


def extract_paddle_boxes(payload: Any) -> list[dict[str, Any]]:
    boxes: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        texts = payload.get("rec_texts") or payload.get("texts") or []
        scores = payload.get("rec_scores") or payload.get("scores") or []
        polys = payload.get("rec_polys") or payload.get("dt_polys") or payload.get("polys") or []
        if isinstance(texts, list) and isinstance(polys, list):
            for idx, text in enumerate(texts):
                bbox = normalize_polygon(polys[idx]) if idx < len(polys) else None
                if not bbox:
                    continue
                confidence = float(scores[idx]) if idx < len(scores) else None
                boxes.append({
                    "text": str(text).strip(),
                    "confidence": confidence,
                    "bbox": bbox,
                })
    return [item for item in boxes if item["text"]]


def run_paddleocr(image: Path, out_dir: Path) -> dict[str, Any]:
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as exc:
        return {
            "engine": "paddleocr",
            "status": "skipped",
            "error": f"paddleocr import failed: {exc}",
            "text_boxes": [],
        }

    raw_dir = out_dir / "paddleocr_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    try:
        ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            engine="paddle",
        )
        result = ocr.predict(str(image))
        raw_records: list[Any] = []
        boxes: list[dict[str, Any]] = []
        for idx, res in enumerate(result):
            if hasattr(res, "save_to_json"):
                res.save_to_json(str(raw_dir))
            payload = getattr(res, "json", None)
            if callable(payload):
                payload = payload()
            if payload is None and isinstance(res, dict):
                payload = res
            if payload is None:
                payload = {"repr": repr(res)}
            raw_records.append(payload)
            boxes.extend(extract_paddle_boxes(payload))
            write_json(raw_dir / f"result_{idx + 1:02d}.json", payload)
        return {
            "engine": "paddleocr",
            "status": "ok",
            "raw_dir": str(raw_dir),
            "text_boxes": boxes,
            "raw_text": " ".join(item["text"] for item in boxes),
            "raw_record_count": len(raw_records),
        }
    except Exception as exc:
        return {
            "engine": "paddleocr",
            "status": "error",
            "error": str(exc),
            "text_boxes": [],
        }


def run_mineru(image: Path, out_dir: Path, backend: str) -> dict[str, Any]:
    if shutil.which("mineru") is None:
        return {
            "engine": "mineru",
            "status": "skipped",
            "error": "mineru executable was not found on PATH",
            "text_boxes": [],
        }
    mineru_out = out_dir / "mineru_raw"
    mineru_out.mkdir(parents=True, exist_ok=True)
    cmd = ["mineru", "-p", str(image), "-o", str(mineru_out), "-b", backend]
    proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "engine": "mineru",
        "status": "ok" if proc.returncode == 0 else "error",
        "command": cmd,
        "returncode": proc.returncode,
        "raw_dir": str(mineru_out),
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "text_boxes": [],
    }


def merge_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int, int, int]] = set()
    for candidate in candidates:
        engine = candidate.get("engine", "unknown")
        for box in candidate.get("text_boxes", []):
            bbox = box.get("bbox") or [0, 0, 0, 0]
            key = (str(box.get("text", "")).strip(), *[int(v) for v in bbox])
            if not key[0] or key in seen:
                continue
            seen.add(key)
            merged.append({
                "text": key[0],
                "bbox": list(key[1:]),
                "confidence": box.get("confidence"),
                "sources": [engine],
            })
    merged.sort(key=lambda item: (item["bbox"][1], item["bbox"][0], item["bbox"][2]))
    return {
        "text_boxes": merged,
        "text": "\n".join(item["text"] for item in merged),
        "box_count": len(merged),
    }


def draw_preview(image: Path, out_path: Path, merged: dict[str, Any]) -> None:
    img = Image.open(image).convert("RGB")
    draw = ImageDraw.Draw(img)
    for item in merged.get("text_boxes", []):
        x, y, w, h = [int(v) for v in item["bbox"]]
        draw.rectangle([x, y, x + w, y + h], outline="#E23D28", width=2)
    img.save(out_path)


def write_report(out_path: Path, candidates: list[dict[str, Any]], merged: dict[str, Any]) -> None:
    lines = [
        "# OCR Review Report",
        "",
        "| Engine | Status | Boxes | Notes |",
        "| --- | --- | ---: | --- |",
    ]
    for candidate in candidates:
        note = candidate.get("error") or candidate.get("stderr") or candidate.get("raw_dir") or ""
        note = str(note).replace("\n", " ")[:160]
        lines.append(
            f"| {candidate.get('engine')} | {candidate.get('status')} | "
            f"{len(candidate.get('text_boxes', []))} | {note} |"
        )
    lines.extend([
        "",
        f"- Merged boxes: {merged.get('box_count', 0)}",
        "",
        "## Merged Text",
        "",
        "```text",
        merged.get("text", ""),
        "```",
        "",
        "Use this as evidence for text masks and content review. Do not treat OCR boxes as final visual asset boundaries.",
    ])
    out_path.write_text("\n".join(lines) + "\n", "utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OCR engines and write OCR-racing artifacts for Image Split.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--engines", default="tesseract", help="Comma-separated engines: tesseract,paddleocr,mineru")
    parser.add_argument("--lang", default="eng+chi_sim", help="Tesseract language string, e.g. eng, chi_sim, eng+chi_sim")
    parser.add_argument("--psm", type=int, default=6, help="Tesseract page segmentation mode.")
    parser.add_argument("--min-conf", type=float, default=30.0, help="Minimum Tesseract confidence from 0 to 100.")
    parser.add_argument("--mineru-backend", default="pipeline", help="MinerU backend, e.g. pipeline.")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    engines = split_engines(args.engines)
    candidates: list[dict[str, Any]] = []
    for engine in engines:
        if engine == "tesseract":
            candidates.append(run_tesseract(args.image, args.lang, args.psm, args.min_conf))
        elif engine == "paddleocr":
            candidates.append(run_paddleocr(args.image, args.out))
        elif engine == "mineru":
            candidates.append(run_mineru(args.image, args.out, args.mineru_backend))
        else:
            candidates.append({
                "engine": engine,
                "status": "skipped",
                "error": f"unsupported engine: {engine}",
                "text_boxes": [],
            })

    merged = merge_candidates(candidates)
    write_json(args.out / "ocr-candidates.json", {
        "source": str(args.image),
        "engines": engines,
        "candidates": candidates,
    })
    write_json(args.out / "ocr-merged.json", {
        "source": str(args.image),
        **merged,
    })
    write_report(args.out / "ocr-review-report.md", candidates, merged)
    draw_preview(args.image, args.out / "ocr_boxes_preview.png", merged)
    print(json.dumps({
        "out": str(args.out),
        "engines": engines,
        "merged_boxes": merged.get("box_count", 0),
        "report": str(args.out / "ocr-review-report.md"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
