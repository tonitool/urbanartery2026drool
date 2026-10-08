#!/usr/bin/env python3
"""Render the UGC feed: put a real stencil onto the blank panel in each snapshot.

The snapshots in ugc/rooms/ are AI-generated casual phone photos with an empty
concrete board. composite.py finds the board and sprays the artwork onto it in
perspective; this script crops the artwork to the board's shape first, so it is
never stretched.

    python3 mockups/ugc/render_ugc.py               # all scenes in scenes.json
    python3 mockups/ugc/render_ugc.py 04-green-flash --debug
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from composite import composite, detect_panel  # noqa: E402

ART_ROOT = Path.home() / "Downloads" / "magdown"
OUT_DIR = HERE.parent.parent / "media"
MAX_WIDTH = 1200
JPEG_QUALITY = 86


def crop_to_aspect(art: np.ndarray, aspect: float) -> np.ndarray:
    """Centre-crop the artwork to width/height = aspect."""
    h, w = art.shape[:2]
    if w / h > aspect:
        new_w = int(h * aspect)
        x = (w - new_w) // 2
        return art[:, x:x + new_w]
    new_h = int(w / aspect)
    y = (h - new_h) // 2
    return art[y:y + new_h]


def quad_aspect(quad: np.ndarray) -> float:
    width = (np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[2] - quad[3])) / 2
    height = (np.linalg.norm(quad[3] - quad[0]) + np.linalg.norm(quad[2] - quad[1])) / 2
    return width / height


def render(name: str, spec: dict, debug: bool) -> Path:
    room = cv2.imread(str(HERE / "rooms" / f"{name}.png"), cv2.IMREAD_COLOR)
    art = cv2.imread(str(ART_ROOT / spec["art"]), cv2.IMREAD_COLOR)
    if room is None or art is None:
        raise SystemExit(f"{name}: could not read room or artwork")
    quad = (np.array(spec["corners"], dtype=np.float32) if "corners" in spec else detect_panel(room))
    art = crop_to_aspect(art, quad_aspect(quad))
    out = composite(room, art, quad, knockout=True)
    for x0, y0, x1, y1 in spec.get("keep", []):  # objects in front of the board
        out[y0:y1, x0:x1] = room[y0:y1, x0:x1]
    if "crop" in spec:  # trim camera overlays such as timestamps
        x0, y0, x1, y1 = spec["crop"]
        out = out[y0:y1, x0:x1]
    if out.shape[1] > MAX_WIDTH:
        scale = MAX_WIDTH / out.shape[1]
        out = cv2.resize(out, (MAX_WIDTH, round(out.shape[0] * scale)), interpolation=cv2.INTER_AREA)
    path = OUT_DIR / f"ua-ugc-{name[3:]}.jpg"
    cv2.imwrite(str(path), out, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    if debug:
        dbg = room.copy()
        cv2.polylines(dbg, [quad.astype(np.int32)], True, (255, 0, 255), 6)
        cv2.imwrite(str(HERE / f"{name}.debug.jpg"), dbg)
    return path


def main() -> None:
    scenes = json.loads((HERE / "scenes.json").read_text())
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(scenes)
    for name in names:
        try:
            print("wrote", render(name, scenes[name], "--debug" in sys.argv))
        except SystemExit as err:
            print(f"{name}: {err}", file=sys.stderr)


if __name__ == "__main__":
    main()
