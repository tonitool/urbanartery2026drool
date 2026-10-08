# Room mockups

Accurate product photos without a photo shoot. The AI generates only **empty
rooms**; the panel and the artwork are drawn here at true scale, so a 20 × 30 cm
piece really looks 20 × 30 cm and the artwork pixels are never invented.

Why not let the AI draw the panel? Image models ignore absolute sizes: asked for
"20 × 30 cm", they produce 40–50 cm. Calibrating an empty room once and drawing
the panel ourselves is the only way the size selector stays honest.

## Render mockups (free, local)

```bash
pip install opencv-python numpy

# one artwork, every room, every size
python3 mockups/render_set.py artwork.png out/ --orientation quer
python3 mockups/render_set.py stencil.png out/ --orientation hoch --knockout-white

# a single image
python3 mockups/place.py wohnen-usm L quer artwork.png out.jpg
python3 mockups/place.py flur S hoch --blank check.jpg        # empty panel, to check placement
```

`--knockout-white` removes the artwork's background colour (read from its
border) so the LightBeton® concrete shows through, as a sprayed stencil does.
Without it, the artwork covers the panel completely.

Sizes: S 20×30, M 40×60, L 80×120, XL 120×180 cm (`hoch` = portrait,
`quer` = landscape). S leans on the furniture where the room allows it; larger
sizes hang above it.

## Rooms (`rooms.json`)

| Room | Scene | Calibrated against |
| --- | --- | --- |
| `wohnen-usm` | Living room, white USM Haller sideboard | sideboard, 153 cm |
| `wohnen-sofa` | Living room, linen sofa, Artek stool | sofa, 230 cm |
| `essen` | Dining, oak table, Thonet chairs | lowboard, 160 cm (estimated) |
| `schlafen` | Bedroom, linen bedding, oak nightstands | pillow row, ≈155 cm |
| `flur` | Hallway, panelled double door, oak bench | bench, 120 cm |
| `arbeiten` | Office, USM Haller desk, Eames chair | desk back edge, 175 cm |

Each entry stores pixels-per-cm (`ref_px` over `ref_cm`), the furniture top at
the wall (`surface_y`), where art is centred (`center_x`), the hanging gap and,
for leaning S pieces, `lean_x`.

## Add a room (Magnific, Seedream 5 Pro, ~100 credits)

1. `python3 mockups/room_prompts.py` prints the empty-room prompts; add a room to
   `ROOMS` in that file. Keep the camera frontal and put one furniture piece of
   known width against the wall.
2. Generate at 3:4, pick a frontal result with a clean empty wall.
3. Measure the furniture's left/right x and its top y at the wall, add an entry
   to `rooms.json`, and check with `--blank` at S and XL.

`textures/lightbeton.jpg` is the concrete surface, extracted from a generated
panel with the room lighting flattened out. `composite.py` is the older tool that
fills a blank panel already present in a photo; it is still useful for real
photos of hung blanks.
