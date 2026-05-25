FROM python:3.11-slim

ARG INSTALL_PADDLEOCR=0

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ocr.txt requirements-paddleocr.txt ./
RUN python -m pip install --upgrade pip \
  && python -m pip install -r requirements.txt -r requirements-ocr.txt

RUN if [ "$INSTALL_PADDLEOCR" = "1" ]; then \
      python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/ && \
      python -m pip install -r requirements-paddleocr.txt ; \
    fi

CMD ["python", "skills/image-split/scripts/ocr_race.py", "--help"]
