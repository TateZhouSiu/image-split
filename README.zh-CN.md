# Image Split

把平面幻灯片或页面图片拆成可用于编辑重建的透明视觉层。

Image Split 是 image-to-PPT 重建流程里的视觉准备层。它把单张 PNG/JPG 幻灯片拆成命名透明资产、定位元数据、contact sheet、文字遮罩，以及可选的 region schema，供后续工具稳定消费。

## 核心思路

很多截图转 PPT 流程失败，是因为直接把 OCR 框或连通域当成最终结构。Image Split 的规则更严格：

- OCR 只作为文字遮罩证据，不决定最终视觉边界。
- 简单 UI 几何应重绘为干净形状或清晰透明资产。
- logo、图标、图表、照片、复杂示意图等应作为独立命名资产提取。
- 每个生产资产都应对应一个设计语义对象，而不是随机像素碎片。
- QA 产物必须随输出一起生成。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
python skills/image-split/scripts/atomic_asset_split.py \
  --image examples/demo/input.png \
  --elements examples/demo/elements.json \
  --out outputs/demo
```

输出包括：

- `manifest.json`
- 裁剪后的透明 PNG 资产
- `assets_contact_sheet.png`
- `composite_no_text_preview.png`

## OCR 一键部署

OCR 在这里是文字遮罩和内容核对证据，不是最终视觉边界。默认容器化 demo 使用 Tesseract：

前置条件：Docker 与 Compose v2。

```bash
make ocr-demo
```

或：

```bash
docker compose run --rm ocr-demo
```

输出会写到 `examples/demo/ocr/`：

- `ocr-candidates.json`
- `ocr-merged.json`
- `ocr-review-report.md`
- `ocr_boxes_preview.png`

如果需要更重的多语言 OCR，可启用 PaddleOCR：

```bash
make ocr-paddle-demo
```

OCR 工具矩阵、部署说明和 MinerU 接入见 [docs/ocr-tools.md](docs/ocr-tools.md)。

## 与 Image-PPT-King 的关系

Image Split 可以独立用于图片视觉资产拆分，也可以作为 Image-PPT-King 的第一阶段：

```text
平面图片 -> Image Split 资产/schema/OCR 证据 -> Image-PPT-King -> 可编辑 PPTX
```
