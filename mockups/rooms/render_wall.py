#!/usr/bin/env python3
"""Draw the four sizes (S, M, L, XL) onto the straight-on wall photo at true scale.

The wall is shot frontally, so one scale holds for the whole wall plane. It is measured
from the sideboard that stands flush against the wall (75 cm high).

    python3 mockups/rooms/render_wall.py
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / "media" / "ua-wall-sizes.jpg"
SPEC = HERE / "wall.json"
JPEG_QUALITY = 88
SIZES_CM = {"S": (20, 30), "M": (40, 60), "L": (80, 120), "XL": (120, 180)}


def crop_to_aspect(art: np.ndarray, aspect: float) -> np.ndarray:
    h, w = art.shape[:2]
    if w / h > aspect:
        new_w = int(h * aspect)
        x = (w - new_w) // 2
        return art[:, x:x + new_w]
    new_h = int(w / aspect)
    y = (h - new_h) // 2
    return art[y:y + new_h]


def add_shadow(wall: np.ndarray, x: int, y: int, w: int, h: int, px_per_cm: float) -> np.ndarray:
    """Soft contact shadow, offset down-right as the daylight comes from the left."""
    blur = max(3, int(px_per_cm * 4)) | 1
    off = int(px_per_cm * 1.5)
    mask = np.zeros(wall.shape[:2], np.float32)
    mask[y + off:y + h + off, x + off:x + w + off] = 1
    mask = cv2.GaussianBlur(mask, (blur, blur), 0) * 0.32
    return (wall * (1 - mask[..., None])).astype(np.uint8)


def hang(wall: np.ndarray, art: np.ndarray, piece: dict, scale: dict) -> tuple[np.ndarray, dict]:
    ppc = scale["px_per_cm"]
    w_cm, h_cm = SIZES_CM[piece["size"]]
    if piece.get("format") == "Querformat":
        w_cm, h_cm = h_cm, w_cm
    w, h = round(w_cm * ppc), round(h_cm * ppc)
    cx = round(piece["center_x"] * scale["width_factor"])
    bottom = round(scale["floor_y"] - piece["bottom_cm"] * ppc)
    x, y = cx - w // 2, bottom - h
    wall = add_shadow(wall, x, y, w, h, ppc)
    face = cv2.resize(crop_to_aspect(art, w / h), (w, h), interpolation=cv2.INTER_AREA)
    edge = max(2, round(ppc * 1.2))  # canvas depth on the right, slightly darker
    wall[y:y + h, x + w:x + w + edge] = (face[:, -1:].astype(np.float32) * 0.78).astype(np.uint8)
    wall[y:y + h, x:x + w] = face
    point = {"size": piece["size"], "x": round((x + w / 2) / wall.shape[1] * 100, 1), "y": round((y + h / 2) / wall.shape[0] * 100, 1)}
    return wall, point


def main() -> None:
    spec = json.loads(SPEC.read_text())
    wall = cv2.imread(str(HERE / "raw" / spec["wall"]), cv2.IMREAD_COLOR)
    if wall is None:
        raise SystemExit("missing wall image")
    factor = wall.shape[1] / spec["measured_width"]  # measurements were taken on the 1x render
    scale = {"px_per_cm": spec["px_per_cm"] * factor, "floor_y": spec["floor_y"] * factor, "width_factor": factor}
    points = []
    for piece in spec["pieces"]:
        art = cv2.imread(str(HERE / "art" / piece["art"]), cv2.IMREAD_COLOR)
        if art is None:
            raise SystemExit(f"missing artwork {piece['art']}")
        wall, point = hang(wall, art, piece, scale)
        points.append({**point, "title": piece["title"]})
    cv2.imwrite(str(OUT), wall, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    print(OUT)
    print(json.dumps(points, ensure_ascii=False))


if __name__ == "__main__":
    main()
