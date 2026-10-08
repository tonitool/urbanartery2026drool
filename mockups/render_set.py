#!/usr/bin/env python3
"""Render one artwork into every calibrated room, at every size that fits.

    python3 mockups/render_set.py artwork.png out_dir/ --orientation quer
    python3 mockups/render_set.py stencil.png out_dir/ --orientation hoch --knockout-white --rooms wohnen-usm flur

Writes out_dir/<artwork>-<room>-<orientation>-<size>.jpg plus out_dir/overview.jpg.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from place import HERE, SIZES_CM, load_room, render, save  # noqa: E402

THUMB_HEIGHT = 560


def overview(paths: list[Path], out: Path) -> None:
    thumbs = []
    for p in paths:
        im = cv2.imread(str(p))
        thumbs.append(cv2.resize(im, (round(im.shape[1] * THUMB_HEIGHT / im.shape[0]), THUMB_HEIGHT)))
    cols = 4
    rows = [thumbs[i:i + cols] for i in range(0, len(thumbs), cols)]
    width = max(sum(t.shape[1] for t in r) for r in rows)
    sheet = np.full((THUMB_HEIGHT * len(rows), width, 3), 255, np.uint8)
    for r, row in enumerate(rows):
        x = 0
        for t in row:
            sheet[r * THUMB_HEIGHT:(r + 1) * THUMB_HEIGHT, x:x + t.shape[1]] = t
            x += t.shape[1]
    save(sheet, out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("artwork", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--orientation", choices=("hoch", "quer"), required=True)
    ap.add_argument("--sizes", nargs="+", choices=SIZES_CM, default=list(SIZES_CM))
    ap.add_argument("--rooms", nargs="+")
    ap.add_argument("--knockout-white", action="store_true")
    args = ap.parse_args()

    art = cv2.imread(str(args.artwork), cv2.IMREAD_COLOR)
    if art is None:
        raise SystemExit(f"Cannot read {args.artwork}")
    rooms = args.rooms or list(json.loads((HERE / "rooms.json").read_text()))
    args.out_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for room_name in rooms:
        cfg, room = load_room(room_name)
        for size in args.sizes:
            try:
                image = render(room, cfg, size, args.orientation, art, args.knockout_white)
            except SystemExit as reason:
                print(f"skip {room_name} {size}: {reason}")
                continue
            path = args.out_dir / f"{args.artwork.stem}-{room_name}-{args.orientation}-{size}.jpg"
            save(image, path)
            written.append(path)
            print(f"wrote {path}")
    if written:
        overview(written, args.out_dir / "overview.jpg")


if __name__ == "__main__":
    main()
