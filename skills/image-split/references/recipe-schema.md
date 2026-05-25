# Component Layer Recipe Schema

Use this schema with `scripts/component_layer_split.py`.

## Top-Level

```json
{
  "layers": []
}
```

Each layer becomes one full-canvas transparent PNG.

## Draw Layer

```json
{
  "name": "layer_name",
  "type": "draw",
  "items": []
}
```

Supported `items`:

- `line`: `{"shape":"line","points":[x0,y0,x1,y1],"fill":"#0052AA","width":3}`
- `rect`: `{"shape":"rect","box":[x0,y0,x1,y1],"fill":"#0052AA","outline":"#0052AA","width":2}`
- `rounded_rect`: `{"shape":"rounded_rect","box":[x0,y0,x1,y1],"radius":12,"fill":"#0052AA","outline":"#0052AA","width":2}`
- `circle`: `{"shape":"circle","center":[x,y],"radius":30,"fill":"#0052AA","outline":"#0052AA","width":2}`
- `ellipse`: `{"shape":"ellipse","box":[x0,y0,x1,y1],"fill":"#0052AA","outline":"#0052AA","width":2}`
- `polygon`: `{"shape":"polygon","points":[[x0,y0],[x1,y1],[x2,y2]],"fill":"#0052AA","outline":"#0052AA"}`
- `arrow`: `{"shape":"arrow","from":[x0,y0],"to":[x1,y1],"fill":"#0052AA","width":16,"head":24}`
- `dashed_line`: `{"shape":"dashed_line","points":[x0,y0,x1,y1],"fill":"#0052AA","width":2,"dash":8,"gap":8}`
- `dashed_rounded_rect`: `{"shape":"dashed_rounded_rect","box":[x0,y0,x1,y1],"radius":14,"outline":"#0052AA","width":2,"dash":8,"gap":8}`

Use hex colors. Alpha is optional as `alpha` from 0-255.

## Extract Layer

```json
{
  "name": "source_art_no_text",
  "type": "extract",
  "mask": "foreground",
  "regions": [[x0, y0, x1, y1]],
  "subtract_text": true,
  "close": 3,
  "dilate": 0,
  "blur_alpha": true
}
```

Masks:

- `foreground`: general blue/color/dark/pale-blue visual pixels.
- `lineart`: thin pale blue decorative strokes; avoids broad white-ish blocks.
- `region`: all pixels inside the listed regions.

Controls:

- `subtract_text`: subtract OCR text mask from this layer.
- `close`: morphological close kernel size. Use `3` or `5`.
- `dilate`: expand mask by this many iterations.
- `blur_alpha`: soften alpha edges. Usually `true`.

## OCR Input

The script accepts OCR JSON in either of these forms:

- `{"slides":[{"slide":3,"text_boxes":[{"text":"...","bbox":[x,y,w,h]}]}]}`
- `[{"text":"...","bbox":[x,y,w,h]}]`

`bbox` uses a 960x540 coordinate system by default and is scaled to the source image size. If OCR coordinates are already in source pixels, pass `--ocr-width` and `--ocr-height` equal to the image dimensions.

## Output

The output folder contains:

- one PNG per layer
- `manifest.json`
- `assets_contact_sheet.png`
- `composite_no_text_preview.png`
- `text_mask_for_reference.png` when OCR is provided

## Atomic Asset Output

For production editable-PPT work, a split may output cropped transparent assets instead of only full-canvas layers. Each cropped asset must be recorded in `manifest.json` with placement metadata:

```json
{
  "file": "card_tl_outline.png",
  "name": "card_tl_outline",
  "type": "drawn-shape",
  "placement": "crop",
  "position": [95, 132, 328, 276],
  "canvas": [1672, 941],
  "slideSize": [960, 540]
}
```

Rules:

- `position` is `[x, y, w, h]` in source-image pixels.
- Simple UI assets should be cropped and positioned, not full-canvas.
- Full-canvas assets are reserved for page-wide backgrounds, footer bands, line-art fields, or compatibility previews.
- UI geometry such as rounded rectangles, circles, pills, arrows, and dashed rules should use clean drawing; do not extract them from the bitmap unless there is no practical alternative.
- Set `blur_alpha: false` for UI/geometry assets. Blurred alpha is allowed only for photos, illustrations, smoke/glow effects, or other soft raster content.

## Atomic Elements File

Use this pattern with `scripts/atomic_asset_split.py`. Coordinates are source-image pixels.

Top-level:

```json
{
  "route": "atomic-assets",
  "canvas": [1672, 941],
  "slideSize": [960, 540],
  "background": "#F7F8F7",
  "assets": []
}
```

Draw asset:

```json
{
  "name": "pharma_icon_emt_ring",
  "type": "draw",
  "kind": "icon-ring",
  "position": [1248, 592, 88, 88],
  "items": [
    {"shape": "circle", "center": [44, 44], "radius": 42, "outline": "#004EA2", "width": 4}
  ],
  "atomic": true
}
```

Crop asset:

```json
{
  "name": "pharma_icon_emt_glyph",
  "type": "crop",
  "kind": "icon-glyph",
  "position": [1265, 614, 55, 48],
  "mask": "color",
  "color": "#004EA2",
  "threshold": 62,
  "soft": 28,
  "atomic": true
}
```

Crop masks supported by `atomic_asset_split.py`:

- `nonwhite`: foreground extraction against a pale background.
- `light`: pale/white line art or glyphs on a deep color background.
- `color`: single-color glyphs on pale backgrounds; set `color`.
- `alpha`: keep existing alpha channel.

Other crop controls:

- `clipEllipse: true`: constrain alpha to an ellipse.
- `erase`: list of local rectangles to clear or fill after crop.
- `trim`: trim transparent bounds; normally avoid for positioned assets unless the manifest position is also adjusted.

V2 circular icon rule:

- Use one drawn asset for the circle/ring/base.
- Use one tight crop asset for the internal glyph.
- Never accept a contact-sheet tile that shows a complete circular icon with background residue when it could be split into base + glyph.
