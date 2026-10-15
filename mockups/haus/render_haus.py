#!/usr/bin/env python3
"""Hang the artworks on the blank canvases of the "Urban Artery Haus" scenes.

Reads haus.json (corners measured on the 2752 px working copies in work/), writes
media/ua-haus-<scene>.jpg and stores each piece's point position (% of the image) back in
haus.json for the homepage settings.

    python3 mockups/haus/render_haus.py [scene ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from composite import composite  # noqa: E402
from rooms.render_rooms import fit_to_aspect  # noqa: E402
from ugc.render_ugc import crop_to_aspect, quad_aspect  # noqa: E402

ART_DIR = HERE.parent / "rooms" / "art"
OUT_DIR = HERE.parent.parent / "media"
JPEG_QUALITY = 84


def render(name: str, spec: dict) -> Path:
    scene = cv2.imread(str(HERE / "work" / f"{name}.png"), cv2.IMREAD_COLOR)
    if scene is None:
        raise SystemExit(f"{name}: missing work/{name}.png")
    h, w = scene.shape[:2]
    for piece in spec["pieces"]:
        art = cv2.imread(str(ART_DIR / piece["art"]), cv2.IMREAD_COLOR)
        if art is None:
            raise SystemExit(f"{name}: missing artwork {piece['art']}")
        quad = np.array(piece["corners"], dtype=np.float32)
        aspect = quad_aspect(quad)
        art = fit_to_aspect(art, aspect) if piece["format"] == "Querformat" else crop_to_aspect(art, aspect)
        scene = composite(scene, art, quad, knockout=False)
        br = quad[2]
        piece["x"], piece["y"] = round(float(br[0] / w * 100), 1), round(float(br[1] / h * 100), 1)
    path = OUT_DIR / f"ua-haus-{name}.jpg"
    cv2.imwrite(str(path), scene, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY, cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
    return path


if __name__ == "__main__":
    haus = json.loads((HERE / "haus.json").read_text())
    for name in sys.argv[1:] or haus:
        print(render(name, haus[name]))
    (HERE / "haus.json").write_text(json.dumps(haus, indent=1, ensure_ascii=False))
