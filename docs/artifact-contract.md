# Artifact Contract

Image Split outputs are designed to be consumed by PPT reconstruction tools.

## Required Files

- `manifest.json`: asset list, canvas size, route, and positioning metadata.
- `assets_contact_sheet.png`: visual review sheet for extracted assets.
- `composite_no_text_preview.png`: reassembled visual preview without semantic text.

## Atomic Asset Record

Each cropped production asset should include:

```json
{
  "file": "01_header_chrome.png",
  "name": "header_chrome",
  "type": "draw",
  "placement": "crop",
  "position": [0, 0, 960, 64],
  "canvas": [960, 540],
  "slideSize": [960, 540],
  "atomic": true
}
```

## Quality Gate

An asset is acceptable only when it represents an intentional visual object, has a real alpha channel, and can be placed back on the source canvas without visible missing geometry outside text-removal zones.
