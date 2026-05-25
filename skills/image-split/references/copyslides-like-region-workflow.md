# CopySlides-Like Region Workflow

Use this route for AI-generated slide images where a previous OCR/inpaint or visual-skeleton approach produced residual text, patch artifacts, fuzzy components, or false QA passes.

## Principle

Do not use a full-page textless/inpainted image as the production visual base. First describe the page as semantic regions, then rebuild regular UI geometry and extract only genuinely complex visuals.

The production output should be:

- clean drawn UI/chrome assets for backgrounds, header lines, cards, tabs, badges, arrows, dividers, footers, and page-number slots
- cropped transparent image assets for illustrations, icons/glyphs, photos, microscopy, charts, and dense figures
- no semantic body/title/card text inside visual layers, except documented logo/chart/photo text
- a `region-schema.json` that `image-ppt` can use to place editable text by visual anchors

This route is closer to a local, auditable CopySlides-style reconstruction than to OCR masking. The schema decides what an object means; OpenCV/OCR only help measure or crop.
When text or layout is dense, add OCR-racing evidence from Apple Vision, PaddleOCR/PP-Structure, MinerU, or another approved local engine, then merge it into the schema. Do not choose the first engine result as final placement.

## Region Schema

Create a schema before cutting assets:

```json
{
  "slide": 16,
  "route": "copyslides-like-region-reconstruction",
  "canvas": [1672, 941],
  "slideSize": [960, 540],
  "regions": [
    {
      "id": "title",
      "type": "text",
      "box": [90, 25, 1325, 60],
      "anchor": "header-baseline",
      "editable": true
    },
    {
      "id": "card_01",
      "type": "card",
      "box": [47, 319, 254, 474],
      "tabBox": [78, 337, 191, 45],
      "badgeCenter": [172, 296],
      "bodyBox": [70, 622, 203, 145],
      "editableText": true,
      "visualMethod": "draw-card-tab-badge"
    },
    {
      "id": "card_01_illustration",
      "type": "illustration",
      "box": [82, 420, 178, 162],
      "visualMethod": "extract-transparent"
    }
  ]
}
```

Use source-canvas coordinates. Keep region ids stable; text specs and QA reports should reference these ids.

Recommended region fields:

- `id`: stable semantic id used by manifests and text specs
- `type`: `text`, `card`, `tab`, `badge`, `connector`, `chart`, `photo`, `illustration`, `footer`, `page_number`, or `chrome`
- `box`: source-canvas box `[x, y, w, h]` or `[x1, y1, x2, y2]`, consistently documented
- `anchor`: placement anchor such as `center`, `inner-padding`, `baseline`, `footer-slot`, or `chart-frame`
- `editable`: whether text should be rebuilt in `image-ppt`
- `visualMethod`: `draw`, `extract-transparent`, `preserve-image`, or `native-shape`
- `textStyle`: optional style-table key for `image-ppt`
- `ocrSources`: merged OCR candidate ids supporting the text/content
- `confidence`: confidence for type, box, and text; mark conflicts for review

## Asset Strategy

Draw these instead of cropping them:

- slide background and header/footer chrome
- card outlines and rounded tabs
- badges and badge circles
- arrows, connectors, rules, dashed dividers
- simple circles/rings/pills behind icons

Extract these from the source:

- internal icon glyphs, cropped tightly without their ring/pill background
- biological/medical illustrations
- microscopy/photos/figure panels
- dense charts when redrawing would be slower than preserving as an image
- decorative line art that is too expensive to redraw but has no semantic text

For circular icon UI, draw the circle/ring and crop only the glyph. Contact sheets should not show a full circular bitmap with background residue unless it is a logo/photo.

## Required Artifacts

For every slide processed through this route, output:

- `region-schema.json`
- `ocr-candidates.json`, `ocr-merged.json`, and `ocr-review-report.md` for text-heavy or high-risk pages
- `visual-layers/第NN页/manifest.json`
- `visual-layers/第NN页/assets_contact_sheet.png`
- `visual-layers/第NN页/composite_no_text_preview.png`
- `visual-layers/第NN页/text_mask_for_reference.png`
- source/composite or source/render side-by-side review image

`manifest.json` must include route `copyslides-like-region-reconstruction`, asset count, asset names, source/drawn type, original-canvas position, canvas size, slide size, and limitations.

Also output a side-by-side source/composite review. If the composite looks clean only because text zones are ignored, the split is not ready.

## Review Checklist

Before handing assets to `image-ppt`:

- The composite has no title/body/card text and no inpaint glyph residue.
- Textless-layer OCR or manual zoom review does not find residual editable text in visual layers.
- Every card, tab, badge, line, arrow, footer, and primary icon exists and is crisp.
- Contact sheet tiles are meaningful objects, not connected-component fragments.
- Complex illustrations are complete and not missing edge pixels.
- No full-page textless/inpaint layer is used as a production asset.
- Any broad layer is limited to true background, footer line art, or documented dense figure/photo content.
- Text-removal regions do not hide broken UI geometry that must be rebuilt.
- The contact sheet shows minimum meaningful objects: one card outline, one tab, one badge/ring, one glyph, one connector, one figure region, etc., rather than broad patches.

## Stop Conditions

Stop before PPT assembly if:

- the schema is missing or does not describe primary layout regions,
- semantic text remains in visual layers,
- a visual asset contains a visible patch, halo, or broken shape,
- a full-slide inpaint layer is required to make the page look complete,
- or a region cannot be mapped to a stable text anchor.

## Validated Page-16 Pattern

For the accepted page-16 sample, the route was:

1. Write `region-schema-slide16.json` for title chrome, flow labels, four card groups, experiment illustrations, footer, and page number.
2. Rebuild background/header/footer, cards, tabs, badge circles, arrows, and dotted connectors as clean visual assets.
3. Extract only complex biological illustrations as image assets.
4. Leave all title/card/tab/badge/body/page-number text to `image-ppt`.
5. Reject full-page inpaint or textless skeleton layers as production assets.

Use the same decision pattern for other dense pages, while allowing different asset counts by page complexity.
