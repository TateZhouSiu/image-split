.PHONY: ocr-demo ocr-shell ocr-paddle-demo

ocr-demo:
	docker compose run --rm ocr-demo

ocr-shell:
	docker compose run --rm ocr-shell

ocr-paddle-demo:
	INSTALL_PADDLEOCR=1 OCR_ENGINES=tesseract,paddleocr docker compose run --rm --build ocr-demo
