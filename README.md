# Image Split

Split flat slide or page images into editable-ready visual layers.

Image Split is the visual-preparation layer for image-to-PPT reconstruction. It turns a single PNG/JPG slide into named transparent assets, placement metadata, contact sheets, text masks, and optional region schemas that downstream tools can trust.

## Why It Exists

Most screenshot-to-PPT workflows fail because they treat OCR boxes or connected components as the source of truth. Image Split uses a stricter contract:

- OCR is evidence for text masks, not the final visual boundary.
- Simple UI geometry is redrawn as clean shapes or crisp transparent assets.
- Complex visuals such as logos, icons, charts, photos, diagrams, and illustrations are extracted as separately named assets.
- Every production asset should map to an intentional design object, not an arbitrary pixel fragment.
- QA artifacts are part of the output, not an afterthought.

## Pipeline

```mermaid
flowchart LR
  A["slide image"] --> B["inspect visual regions"]
  B --> C["atomic elements / recipe"]
  C --> D["transparent assets"]
  C --> E["manifest.json"]
  C --> F["contact sheet + composite preview"]
  E --> G["Image-PPT-King or other renderer"]
```

## Reproducibility Profile

The bundled script demo is deterministic and does not require an AI model. Production-quality splitting of real slide screenshots does require a capable agent runtime because the hard part is deciding semantic regions, visual anchors, OCR conflicts, and QA gates.

Recommended agent runtime:

- Codex-style agent mode with local file read/write and command execution.
- Multimodal model with image input and strong visual reasoning.
- Frontier reasoning model, such as GPT-5.5 or an equivalent model, for dense or high-value decks.
- Reasoning effort: `high` for normal production work; `xhigh` when available for difficult full-deck reconstruction.
- Long enough context to inspect source images, manifests, OCR evidence, contact sheets, and generated artifacts together.

Known-good author setup: macOS, Codex-style local agent, GPT-5.5-class multimodal reasoning, and `xhigh` reasoning for difficult pages. Smaller or lower-reasoning models can still run the scripts, but may need more human correction when authoring region schemas or judging split quality.

## Quick Start

Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the atomic asset splitter:

```bash
python skills/image-split/scripts/atomic_asset_split.py \
  --image examples/demo/input.png \
  --elements examples/demo/elements.json \
  --out outputs/demo
```

The command writes:

- `manifest.json`
- cropped transparent PNG assets
- `assets_contact_sheet.png`
- `composite_no_text_preview.png`

## Platform Notes

The repository is authored and validated primarily on macOS. The scripts are cross-platform Python, but shell setup differs:

- macOS/Linux/WSL2: use the commands as written with `python -m venv`, `source .venv/bin/activate`, and POSIX line continuations.
- Windows PowerShell: use `py -m venv .venv`, then `.venv\Scripts\Activate.ps1`, then `pip install -r requirements.txt`.
- Windows users who need OCR or PaddleOCR should prefer WSL2 with Docker Desktop integration. Native Windows can run the Python scripts, but `make ocr-demo` normally requires either GNU Make or the direct command `docker compose run --rm ocr-demo`.
- Direct host OCR requires the Tesseract binary on `PATH`; the Docker OCR path is the most repeatable option across machines.

## OCR One-Command Setup

OCR is used as evidence for text masks and content review. The default containerized OCR demo uses Tesseract:

Prerequisite: Docker with Compose v2.

```bash
make ocr-demo
```

or:

```bash
docker compose run --rm ocr-demo
```

This writes `ocr-candidates.json`, `ocr-merged.json`, `ocr-review-report.md`, and `ocr_boxes_preview.png` under `examples/demo/ocr/`.

Optional PaddleOCR support is available when you want a heavier multilingual OCR engine:

```bash
make ocr-paddle-demo
```

See [docs/ocr-tools.md](docs/ocr-tools.md) for the OCR tool matrix, deployment notes, and MinerU integration.

## Routes

- `atomic-assets`: preferred production route. Outputs cropped transparent assets with `position` and `canvas` metadata.
- `copyslides-like region`: creates a semantic region schema first, then uses it as the contract for extraction and PPT reconstruction.
- `visual-skeleton`: quick preview route using broader full-canvas layers. Useful for layout checks, not final editable reconstruction.

## Skill

The reusable agent skill lives at:

```text
skills/image-split/SKILL.md
```

For Codex-style skill installation, copy `skills/image-split/` into your local skills directory and restart the agent.

The skill folder is also self-contained for a smoke test:

```bash
cd ~/.codex/skills/image-split
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/atomic_asset_split.py \
  --image assets/demo/input.png \
  --elements assets/demo/elements.json \
  --out outputs/demo
```

The installed skill folder also includes the OCR Docker demo:

```bash
make ocr-demo
```

This writes OCR artifacts to `outputs/ocr-demo/` from the bundled demo image.

## Relationship To Image-PPT-King

Image Split can be used independently for visual asset extraction, but it is also the first stage of Image-PPT-King:

```text
flat image -> Image Split assets/schema/OCR evidence -> Image-PPT-King -> editable PPTX
```

## Status

This repository is an open-source packaging pass over a working local workflow. The public skill folder now includes its own demo assets, Python requirements, OCR references, and Docker-based OCR smoke path; CI remains a useful next step.
