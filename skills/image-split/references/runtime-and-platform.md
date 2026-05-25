# Runtime And Platform

## Agent Runtime

The bundled smoke demo is script-only and deterministic. It does not require an AI model once Python dependencies are installed.

Real slide reconstruction is different. A capable agent must inspect the source image, decide semantic regions, correct OCR evidence, author or patch element recipes, run scripts, and review contact sheets and composites.

Recommended production profile:

- Codex-style agent mode with local file read/write and command execution.
- Multimodal model with image input and strong visual reasoning.
- Frontier reasoning model, such as GPT-5.5 or an equivalent model, for dense or high-value decks.
- Reasoning effort: `high` for normal production work; `xhigh` when available for difficult full-deck reconstruction.
- Enough context to compare source images, manifests, OCR evidence, contact sheets, and generated artifacts.

Known-good author setup: macOS, Codex-style local agent, GPT-5.5-class multimodal reasoning, and `xhigh` reasoning for difficult pages.

## Platform Notes

The author validates primarily on macOS. The scripts are cross-platform Python, but setup commands differ by shell.

macOS/Linux/WSL2:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

For OCR, Docker is the most repeatable path:

```bash
make ocr-demo
```

On native Windows without GNU Make, run:

```powershell
docker compose run --rm ocr-demo
```

For PaddleOCR or heavier OCR stacks on Windows, prefer WSL2 with Docker Desktop integration. Direct host OCR requires the Tesseract binary to be installed and available on `PATH`.
