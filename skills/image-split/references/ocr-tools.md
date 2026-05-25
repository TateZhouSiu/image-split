# OCR Tools

Image Split treats OCR as evidence, not as the source of visual truth. OCR helps locate semantic text, create text masks, and review content conflicts. Final visual boundaries still come from region schemas and visual anchors.

## Tool Matrix

| Tool | Default | Best For | Output Role | Deployment |
| --- | --- | --- | --- | --- |
| Tesseract | Yes | Fast local smoke tests, basic Latin/CJK text boxes | `ocr-candidates.json`, `ocr-merged.json`, preview boxes | Docker image in this repo |
| PaddleOCR | Optional | Higher-quality multilingual OCR and document layouts | OCR racing candidate, optional raw JSON | Build with `INSTALL_PADDLEOCR=1` |
| MinerU | Optional | Complex document parsing for PDF/image/Office inputs | External raw parsing evidence | Install separately or use official Docker |
| Apple Vision | Optional, macOS only | Local macOS OCR evidence | Future adapter / manual evidence | Native macOS only |

## One-Command OCR Demo

From the `image-split` repository root:

Prerequisite: Docker with Compose v2.

```bash
make ocr-demo
```

Equivalent command:

```bash
docker compose run --rm ocr-demo
```

This builds a local OCR container with Tesseract and writes:

- `examples/demo/ocr/ocr-candidates.json`
- `examples/demo/ocr/ocr-merged.json`
- `examples/demo/ocr/ocr-review-report.md`
- `examples/demo/ocr/ocr_boxes_preview.png`

When this skill folder is installed by itself, run the same command from the skill root:

```bash
make ocr-demo
```

The standalone skill demo writes:

- `outputs/ocr-demo/ocr-candidates.json`
- `outputs/ocr-demo/ocr-merged.json`
- `outputs/ocr-demo/ocr-review-report.md`
- `outputs/ocr-demo/ocr_boxes_preview.png`

## Optional PaddleOCR Demo

PaddleOCR is more capable but heavier. Build the optional stack only when needed:

```bash
make ocr-paddle-demo
```

Equivalent command:

```bash
INSTALL_PADDLEOCR=1 OCR_ENGINES=tesseract,paddleocr docker compose run --rm --build ocr-demo
```

The Dockerfile follows the current PaddleOCR 3.x installation model: install an inference engine first, then install `paddleocr`. The default Docker build uses CPU PaddlePaddle.

## Optional MinerU Use

MinerU is useful when the input is closer to a document parsing problem than a simple slide screenshot problem. After installing MinerU in your environment, run:

```bash
python skills/image-split/scripts/ocr_race.py \
  --image examples/demo/input.png \
  --out examples/demo/ocr-mineru \
  --engines mineru \
  --mineru-backend pipeline
```

MinerU's Docker deployment has separate Linux/WSL2 and GPU considerations, so this repo does not make it the default container path.

## Direct Script Usage

From the repository root:

```bash
python skills/image-split/scripts/ocr_race.py \
  --image examples/demo/input.png \
  --out examples/demo/ocr \
  --engines tesseract \
  --lang eng
```

From an installed skill root:

```bash
python scripts/ocr_race.py \
  --image assets/demo/input.png \
  --out outputs/ocr-demo \
  --engines tesseract \
  --lang eng
```

Multiple engines:

```bash
python skills/image-split/scripts/ocr_race.py \
  --image examples/demo/input.png \
  --out examples/demo/ocr \
  --engines tesseract,paddleocr,mineru \
  --lang eng+chi_sim
```

## Public References

- PaddleOCR installation: https://www.paddleocr.ai/main/en/version3.x/installation.html
- PaddleOCR quick start: https://www.paddleocr.ai/latest/en/quick_start.html
- Tesseract installation and command usage: https://github.com/tesseract-ocr/tessdoc/blob/main/Installation.md
- MinerU quick start: https://opendatalab.github.io/MinerU/quick_start/
- MinerU Docker deployment: https://opendatalab.github.io/MinerU/zh/quick_start/docker_deployment/
