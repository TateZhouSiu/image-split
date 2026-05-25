# Image Split Acceptance Rubric

Use this rubric when a split will feed an editable PPT. Treat each gate as `pass`, `warn`, or `fail`. A `fail` blocks PPT assembly unless the user explicitly accepts the limitation.

## Gate S0: Required Artifacts

- `manifest.json` exists and lists every production asset with `name`, `file`, `type`, `position`, `canvas`, and known limitations when applicable.
- `assets_contact_sheet.png`, `composite_no_text_preview.png`, and `text_mask_for_reference.png` exist.
- Important slides also have source/composite/diff or source/composite side-by-side review images.
- `copyslides-like region route` slides also have `region-schema.json` with stable ids, boxes, anchors, editability, and reconstruction method.
- Text-heavy CopySlides-like slides also have `ocr-candidates.json`, `ocr-merged.json`, and `ocr-review-report.md`, or a note explaining why a single OCR/manual transcription route was sufficient.
- Every PNG is RGBA or has a real alpha channel.
- Cropped assets include original-canvas `x/y/w/h`; full-canvas preview layers match the source image dimensions exactly.

Fail if any required artifact is missing, an asset lacks placement metadata, or a PNG has no usable transparency.

## Gate S1: Atomicity And Naming

- Each movable visual object should be its own asset: card outline, tab background, icon glyph, circle/ring, connector, divider, footer, logo, illustration, chart/photo region.
- A typical editable PPT page should usually contain 20-80 meaningful assets. Fewer is acceptable only for simple pages; more is acceptable for dense diagrams if each asset is semantically named.
- Production names must describe design meaning, such as `card_left_outline`, `tab_junyao_bg`, `center_circle`, `footer_lineart`.
- Broad assets are allowed only for true backgrounds, full-width footer line art, chart/photo regions, or documented non-editable complex art.
- In the CopySlides-like route, regular UI geometry should be drawn/rebuilt as clean assets; broad full-page textless or inpainted bitmaps are not production visual assets.

Fail if a production asset named like a group (`all_cards`, `blue_ui`, `source_visuals`) contains unrelated movable UI objects, or if contact sheet tiles look like arbitrary connected-component fragments.

## Gate S2: Visual Fidelity

Compare `composite_no_text_preview.png` against the source while ignoring intended editable-text zones.

- Clean geometry pages: non-text changed pixels over 25 RGB levels should normally be `pass <= 8%`, `warn <= 12%`, `fail > 12%`.
- Complex chart/photo pages may exceed 12%, but the report must explain that the changed area is inside chart/photo/text zones rather than broken UI.
- Header/footer/card/pill/circle anchor positions should be `pass <= 3 px`, `warn <= 6 px`, `fail > 6 px` in 960x540 coordinates.
- Connector endpoints should land within 4 px of their visual anchors; otherwise fix the line or group movement.
- Missing cards, tabs, badges, arrows, page chrome, logo, primary icons, or footer line art are blocking failures.

Fail on visible white patches, blue patches, broken/cropped badges, fuzzy rounded corners, rectangular crop halos, or missing primary visual components.

## Gate S3: Text Removal

- Main semantic text should be absent from visual layers.
- Preserved text must be intentional and documented: logo text, chart axes, microscopy labels, decorative background words, or figure screenshots.
- OCR masks must not cut icons, logos, dashed lines, thin rules, or medical illustrations.
- For high-risk pages, run textless-layer OCR or manual zoom review. Any detected title/body/card/label text that should become editable is a blocking failure.

Fail if title/body/card text remains baked into visual assets, or if text removal visibly damages important non-text visuals.
Fail if a CopySlides-like visual asset preserves residual title/card/body glyphs that will sit underneath editable text.

## Gate S4: OCR And Region Evidence

- OCR racing is used as evidence, not as final geometry. Region schema anchors define final split and text placement.
- Merged OCR should preserve engine disagreements for numbers, units, symbols, Greek letters, and scientific terms.
- Low-confidence or conflicting OCR must be marked `needs-human-review`.
- Region schema should record `ocrSources` and confidence when OCR supports a text region.

Warn if only one OCR/manual source was used on a simple page. Fail if OCR boxes alone define final regions on a difficult page, or if conflicting scientific text is silently accepted.

## Gate S5: Asset Sharpness

- UI assets should have crisp alpha edges. Do not use blurred alpha to hide crop mistakes.
- Cropped assets should have modest transparent padding, typically 2-6 px for icons and 4-10 px for larger components.
- Circular UI must be split into drawn circle/ring plus tight glyph crop unless it is a photo/logo.
- Repeated assets should have consistent stroke width, radius, color, and shadow treatment.

Warn if a tiny glyph is slightly soft but readable. Fail if the contact sheet shows background-colored halos, edge blur, or a full circular bitmap where a split circle/glyph is expected.

## Gate S6: Optimization Safety

For local or v3-style position optimization:

- Do not accept metric improvement alone. Always create whole-slide and zoomed source/previous/current comparisons.
- Lock stable anchors before search: slide margins, header line, footer band, card groups, circle centers, and page number slot.
- Default maximum shift: 6 px for visual assets, 4 px for text-associated visual anchors, unless a manual note explains the exception.
- Move grouped elements together: a card outline, tab, icon, connector endpoint, and related text anchor should not drift independently.

Fail if optimization improves pixel diff but makes a design object visually misaligned, disconnected, or semantically off-center.

## Gate S7: Decision Record

The final response or report must state:

- route used: `atomic-assets`, `visual-skeleton`, `Image2 textless skeleton`, or `hybrid`
- whether a `region-schema.json` was used and whether it is ready for `image-ppt`
- number of assets and pages processed
- pass/warn/fail summary
- known limitations and whether they are acceptable for the next stage

Do not proceed to full-deck PPT assembly when any slide has a blocking split failure.
