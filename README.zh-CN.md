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

## 复现运行画像

仓库内置的脚本 demo 是确定性的，不需要 AI 模型。真正处理复杂真实截图时，难点在于判断语义区域、视觉锚点、OCR 冲突和 QA 门槛，因此需要能力足够强的 agent 运行环境。

推荐运行环境：

- Codex 风格 agent mode，能读写本地文件并执行命令。
- 支持图片输入、视觉理解较强的多模态模型。
- 复杂或高价值整套幻灯片，建议使用 GPT-5.5 或同级 frontier reasoning model。
- reasoning effort：常规生产任务用 `high`；困难整套重建在可用时用 `xhigh`。
- 上下文长度足够同时检查源图、manifest、OCR 证据、contact sheet 和生成产物。

作者已验证环境：macOS、Codex 本地 agent、GPT-5.5 级别多模态推理模型，困难页面使用 `xhigh` reasoning。较小或低推理模型也能跑脚本，但在编写 region schema 或判断拆分质量时，通常需要更多人工修正。

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

## 平台说明

这个仓库主要在 macOS 上编写和验证。脚本是跨平台 Python，但 shell 命令略有差异：

- macOS/Linux/WSL2：可以直接使用 README 中的 `python -m venv`、`source .venv/bin/activate` 和反斜杠换行命令。
- Windows PowerShell：使用 `py -m venv .venv`，然后执行 `.venv\Scripts\Activate.ps1`，再执行 `pip install -r requirements.txt`。
- Windows 用户如果要跑 OCR 或 PaddleOCR，推荐使用 WSL2 + Docker Desktop integration。原生 Windows 可以跑 Python 脚本，但 `make ocr-demo` 通常需要 GNU Make；也可以直接运行 `docker compose run --rm ocr-demo`。
- 直接在宿主机跑 OCR 时，需要把 Tesseract 可执行文件加入 `PATH`；跨机器最稳定的方式仍是 Docker OCR 路径。

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

## Skill 安装复现

如果只安装 skill 目录，也可以直接跑最小 demo：

```bash
cp -R skills/image-split ~/.codex/skills/
cd ~/.codex/skills/image-split
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/atomic_asset_split.py \
  --image assets/demo/input.png \
  --elements assets/demo/elements.json \
  --out outputs/demo
```

单独安装后的 skill 目录也包含 OCR Docker demo：

```bash
make ocr-demo
```

它会基于内置 demo 图片把 OCR 产物写到 `outputs/ocr-demo/`。

## 与 Image-PPT-King 的关系

Image Split 可以独立用于图片视觉资产拆分，也可以作为 Image-PPT-King 的第一阶段：

```text
平面图片 -> Image Split 资产/schema/OCR 证据 -> Image-PPT-King -> 可编辑 PPTX
```
