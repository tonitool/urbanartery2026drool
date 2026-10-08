#!/usr/bin/env python3
"""Render an artwork as a free-standing LightBeton® panel on a transparent background.

For cut-out style sections (floating collage, lineup): the artwork is printed on
the bundled concrete texture with a hairline edge and a soft drop shadow, and the
result is saved as a transparent PNG.

    python3 mockups/packshot.py artwork.png out.png
    python3 mockups/packshot.py stencil.png out.png --knockout-white --width 900
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from place import make_face  # noqa: E402

SHADOW_BLUR = 0.035       # share of panel width
SHADOW_OFFSET = (0.015, 0.03)
SHADOW_OPACITY = 0.38
MARGIN = 0.08             # transparent margin around the panel, share of width


def packshot(art: np.ndarray, width: int, knockout: bool) -> np.ndarray:
    h_art, w_art = art.shape[:2]
    w, h = width, round(width * h_art / w_art)
    face = make_face(w, h, art, knockout).clip(0, 255).astype(np.uint8)
    edge = max(2, w // 300)
    face[:, -edge:] = (face[:, -edge:] * 0.85).astype(np.uint8)
    face[-edge:, :] = (face[-edge:, :] * 0.8).astype(np.uint8)

    m = round(width * MARGIN)
    canvas_h, canvas_w = h + 2 * m, w + 2 * m
    shadow = np.zeros((canvas_h, canvas_w), np.float32)
    dx, dy = round(SHADOW_OFFSET[0] * w), round(SHADOW_OFFSET[1] * w)
    cv2.rectangle(shadow, (m + dx, m + dy), (m + w + dx, m + h + dy), 1.0, -1)
    shadow = cv2.GaussianBlur(shadow, (0, 0), sigmaX=SHADOW_BLUR * w) * SHADOW_OPACITY

    out = np.zeros((canvas_h, canvas_w, 4), np.uint8)
    out[..., 3] = (shadow * 255).astype(np.uint8)
    out[m:m + h, m:m + w, :3] = face
    out[m:m + h, m:m + w, 3] = 255
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("artwork", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--knockout-white", action="store_true")
    args = ap.parse_args()
    art = cv2.imread(str(args.artwork), cv2.IMREAD_COLOR)
    if art is None:
        raise SystemExit(f"Cannot read {args.artwork}")
    if not cv2.imwrite(str(args.out), packshot(art, args.width, args.knockout_white)):
        raise SystemExit(f"Could not write {args.out}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
