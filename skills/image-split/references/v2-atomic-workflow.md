# V2 Atomic Workflow

Use this reference when the user cares about close visual reconstruction and editable PPT output.

## Goal

Produce transparent visual assets that can be recomposed without white/blue patches, fuzzy UI edges, broken circles, or merged multi-object layers.

## Component Grammar

Classify every visible non-text object before extraction:

- `chrome`: header triangle, header rule, footer bar, page number slot, logo.
- `container`: cards, panels, chart frames, rounded rectangles, separators.
- `label-base`: pills, tabs, badges, numbered circles, section tags.
- `icon-base`: deterministic circle, ring, shield background, or icon container.
- `icon-glyph`: the internal symbol only, tightly cropped.
- `connector`: line, dot, arrow, dashed line, dashed arc.
- `line-art`: decorative campus line art, plant line art, background motifs.
- `figure-region`: charts, microscopy, spectra, photos, dense diagrams.

## Preferred Construction

- Draw deterministic UI geometry: cards, pills, rings, circles, rules, dots, arrows, dashed lines, and dashed arcs.
- Crop only complex raster content: logos, glyphs, illustrations, line art, charts, photos.
- Split circular icons into at least two assets:
  - `*_circle_base` or `*_ring`: drawn clean geometry.
  - `*_glyph`: tight transparent crop of the internal symbol.
- Do not crop a whole circular UI icon as one asset unless it is a logo/photo and cannot be decomposed.
- Keep icon glyph crop boxes tight enough that the contact sheet shows no pill edge, background residue, or unrelated circle boundary.
- Use `mask: "light"` for white glyphs/line art on blue backgrounds.
- Use `mask: "color"` for blue glyphs on pale backgrounds.
- Use `mask: "nonwhite"` for logos or line art on pale backgrounds.

## Atomic Elements File Pattern

```json
{
  "route": "atomic-assets",
  "canvas": [1672, 941],
  "slideSize": [960, 540],
  "background": "#F7F8F7",
  "assets": [
    {
      "name": "card_tl_outline",
      "type": "draw",
      "kind": "card-outline",
      "position": [96, 132, 328, 274],
      "items": [
        {"shape": "rounded_rect", "box": [0, 0, 327, 273], "radius": 18, "outline": "#004EA2", "width": 3}
      ],
      "atomic": true
    },
    {
      "name": "tab_tl_icon_circle_base",
      "type": "draw",
      "kind": "icon-base",
      "position": [158, 143, 66, 66],
      "items": [
        {"shape": "circle", "center": [33, 33], "radius": 32, "fill": "#004EA2"}
      ],
      "atomic": true
    },
    {
      "name": "tab_tl_icon_glyph",
      "type": "crop",
      "kind": "icon-glyph",
      "position": [174, 159, 36, 35],
      "mask": "light",
      "threshold": 118,
      "soft": 28,
      "atomic": true
    }
  ]
}
```

## QA Standard

Required artifacts:

- `manifest.json`
- `assets_contact_sheet.png`
- `composite_no_text_preview.png`
- source/composite or source/render side-by-side for representative slides

Blocking failures:

- Contact sheet tile contains multiple unrelated movable objects.
- Full circular icon is cropped as one bitmap when it should be split into base/ring + glyph.
- Glyph crop shows background residue, pill edge, partial circle boundary, or clipped symbol.
- UI geometry is fuzzy, blurred, or has rectangular crop halos.
- Main non-text layout misses a visible icon, connector, card, panel, footer, or logo.

Useful numeric checks:

- For clean geometric pages, non-text changed pixels with RGB delta > 25 should usually stay under 8-12%.
- Use this number as a regression signal only; manual visual review of the contact sheet remains required.

## Stop Condition

Do not proceed to full-deck PPT assembly if a representative slide still has broken circular icons, cropped glyphs, fuzzy card corners, visible patch blocks, or merged component tiles.
