# Region Schema And OCR Racing

Use this reference for text-heavy or previously failed Image2/PPT screenshot pages. The goal is a CopySlides-like intermediate representation that both `image-split` and `image-ppt` can trust.

## Region Schema First

Create `region-schema-slideNN.json` before producing the final PPTX. It is the contract for visual splitting, text placement, and QA.

Minimum top-level fields:

```json
{
  "slide": 16,
  "route": "copyslides-like-region-reconstruction",
  "canvas": {"w": 1672, "h": 941},
  "slideSize": {"w": 960, "h": 540},
  "sourceImage": "/abs/path/slide16.png",
  "coordinateSystem": "source-pixels",
  "regions": []
}
```

Each region should include:

- `id`: stable semantic id, such as `title_main`, `flow_label_01`, `card_03`, `chart_main`, `page_number`.
- `type`: `title`, `body`, `flow_label`, `card`, `tab`, `badge`, `chart`, `microscopy`, `photo`, `image`, `caption`, `footer`, `page_number`, `chrome`, `connector`.
- `box`: source-pixel `{x,y,w,h}`.
- `z`: approximate layer order.
- `editable`: whether semantic text should be rebuilt in PPT.
- `visualMethod`: `draw-native`, `draw-raster`, `extract-image`, `preserve-image`, `text-only`, or `ignore`.
- `nativeShape`: suggested PPT/shape primitive when applicable: `rect`, `roundedRect`, `ellipse`, `line`, `arrow`, `freeform`, `none`.
- `style`: fill/outline/color/radius/stroke hints.
- `anchor`: `center`, `baseline`, `innerBox`, `badgeCenter`, `footerSlot`, `chartFrame`, or custom points.
- `ocrSources`: ids of OCR candidates supporting the region.
- `confidence`: 0-1 confidence for region type, box, and text.
- `notes`: limitations, human overrides, or unresolved conflicts.

## OCR Racing Inputs

Run multiple engines when available and useful:

- Apple Vision: fast local OCR, good first pass on clean screenshots.
- PaddleOCR / PP-Structure: text detection/recognition plus layout, title/text/image/table/chart style evidence.
- MinerU: document/image parsing into structured Markdown/JSON; useful for layout/table/figure evidence on complex pages.
- Tesseract or other OCR may be a fallback, not the primary authority.

Write all raw results to `ocr-candidates.json`:

```json
{
  "engines": [
    {"name": "apple_vision", "version": "local", "status": "ok"},
    {"name": "paddleocr_ppstructure", "version": "local", "status": "ok"}
  ],
  "items": [
    {
      "id": "ocr_001",
      "engine": "apple_vision",
      "text": "细胞实验",
      "box": {"x": 103, "y": 35, "w": 210, "h": 42},
      "confidence": 0.96
    }
  ]
}
```

## Merge Rules

Create `ocr-merged.json` after clustering candidates by geometric overlap and text similarity.

- Text content: prefer agreement across engines; preserve engine-specific candidates when symbols, Greek letters, units, or numbers differ.
- Coordinates: average only close boxes; otherwise snap to `region-schema` anchors or mark conflict.
- Reading order: infer from region type and slide design, not just y/x sort.
- Confidence: lower confidence if engines disagree on content, box, or region type.
- Human review: set `needsHumanReview: true` for low confidence, conflicting numbers/units, or text that would alter scientific meaning.

Do not silently choose the first successful OCR result. If OCR disagrees with the visual region, the region wins for placement and OCR becomes content evidence only.

## Artifacts

For high-risk pages, produce:

- `region-schema-slideNN.json`
- `ocr-candidates.json`
- `ocr-merged.json`
- `ocr-review-report.md`
- `text_mask_for_reference.png`
- `composite_no_text_preview.png`

The report should list missing text, conflicting text, low-confidence regions, and any text intentionally preserved inside figures/logos.

## Failure Conditions

Stop before PPT assembly if:

- no stable region schema exists,
- OCR content conflicts on scientific values and no source document can resolve it,
- OCR masks damage non-text visual elements,
- the textless composite still contains editable title/body/card text,
- or text placement would depend only on raw OCR boxes.

## External Design References

- CopySlides public image-to-presentation material: layout detection, element reconstruction, and editable PPTX output.
- PaddleOCR PP-Structure documentation: layout analysis, text/title/image/table regions, OCR, and table recognition.
- MinerU documentation/GitHub: structured Markdown/JSON output for documents/images and layout-oriented parsing.
- Images2Slides paper: region-level specification, pixel-to-slide coordinate mapping, and native slide recreation.
