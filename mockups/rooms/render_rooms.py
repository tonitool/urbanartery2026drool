#!/usr/bin/env python3
"""Hang real motifs on the blank canvases of the isometric room renders.

    python3 mockups/rooms/render_rooms.py            # every room in rooms.json
    python3 mockups/rooms/render_rooms.py wohnzimmer
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
from ugc.render_ugc import crop_to_aspect, quad_aspect  # noqa: E402

OUT_DIR = HERE.parent.parent / "media"
JPEG_QUALITY = 86
MEASURED_WIDTH = 1376  # corners in rooms.json were read on the 1x renders
BACKDROP = (0x0c, 0x0c, 0x0c)  # BGR of #0c0c0c, the section background
FLOOR_SHARE = 1.0  # share of the room height kept from the top; 1.0 = the whole room
FRAME_ASPECT = 1.5  # every room is padded to the same frame so the section never jumps
SIDE_PAD = 0.035


def backdrop_mask(img: np.ndarray) -> np.ndarray:
    """1.0 where the plain backdrop is, 0.0 on the room (flood fill from the corners)."""
    h, w = img.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    smooth = cv2.GaussianBlur(img, (5, 5), 0)
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        cv2.floodFill(smooth.copy(), mask, seed, 0, (4, 4, 4), (4, 4, 4), cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    return cv2.GaussianBlur(mask[1:-1, 1:-1].astype(np.float32) / 255, (9, 9), 0)


def even_backdrop(img: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Paint the backdrop one flat colour so every room sits on the same ground."""
    flat = np.full_like(img, BACKDROP)
    return (img * (1 - alpha[..., None]) + flat * alpha[..., None]).astype(np.uint8)


def pad_to_frame(img: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Pad with the backdrop colour to FRAME_ASPECT; returns the image and the left/top padding."""
    h, w = img.shape[:2]
    target_w, target_h = max(w, int(h * FRAME_ASPECT)), max(h, int(w / FRAME_ASPECT))
    pad_x, pad_y = (target_w - w) // 2, (target_h - h) // 2
    framed = cv2.copyMakeBorder(img, pad_y, target_h - h - pad_y, pad_x, target_w - w - pad_x,
                                cv2.BORDER_CONSTANT, value=BACKDROP)
    return framed, pad_x, pad_y


def zoom_box(alpha: np.ndarray) -> tuple[int, int, int, int]:
    """Crop to the walls: full room width plus a little air, but only the back of the floor."""
    h, w = alpha.shape
    ys, xs = np.where(alpha < 0.5)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    pad = int(w * SIDE_PAD)
    top = max(0, y0 - pad)
    bottom = min(h, int(y0 + (y1 - y0) * FLOOR_SHARE) + (pad if FLOOR_SHARE >= 1 else 0))
    return max(0, x0 - pad), top, min(w, x1 + pad), bottom


def fit_to_aspect(art: np.ndarray, aspect: float) -> np.ndarray:
    """Show the whole motif: extend it to width/height = aspect by continuing its own edge colours
    (edge pixels stretched outwards, then softened), so the paper tone has no visible seam."""
    h, w = art.shape[:2]
    if w / h < aspect:
        pad = int(h * aspect) - w
        left, right, top, bottom = pad // 2, pad - pad // 2, 0, 0
    else:
        pad = int(w / aspect) - h
        left, right, top, bottom = 0, 0, pad // 2, pad - pad // 2
    out = cv2.copyMakeBorder(art, top, bottom, left, right, cv2.BORDER_REPLICATE)
    k = max(31, (max(out.shape[:2]) // 12) | 1)
    soft = cv2.GaussianBlur(out, (k, k), 0)
    mask = np.zeros(out.shape[:2], np.float32)
    mask[top:top + h, left:left + w] = 1
    band = max(9, (min(h, w) // 10) | 1)
    mask = cv2.GaussianBlur(mask, (band * 2 + 1, band * 2 + 1), 0)[..., None]
    mask[top + band:top + h - band, left + band:left + w - band] = 1
    return (out * mask + soft * (1 - mask)).astype(np.uint8)


def render(name: str, spec: dict) -> Path:
    room = cv2.imread(str(HERE / "raw" / spec["raw"]), cv2.IMREAD_COLOR)
    if room is None:
        raise SystemExit(f"{name}: missing raw render {spec['raw']}")
    out = room
    factor = room.shape[1] / MEASURED_WIDTH
    for piece in spec["pieces"]:
        art_path = HERE / "art" / piece["art"]
        art = cv2.imread(str(art_path), cv2.IMREAD_COLOR)
        if art is None:
            raise SystemExit(f"{name}: missing motif {art_path.name}")
        quad = np.array(piece["corners"], dtype=np.float32) * factor
        aspect = quad_aspect(quad)
        art = fit_to_aspect(art, aspect) if piece["format"] == "Querformat" else crop_to_aspect(art, aspect)
        out = composite(out, art, quad, knockout=False)
    alpha = backdrop_mask(room)
    out = even_backdrop(out, alpha)
    left, top, right, bottom = zoom_box(alpha)
    out = out[top:bottom, left:right]
    out, pad_x, pad_y = pad_to_frame(out)
    for piece in spec["pieces"]:  # points sit at each canvas' lower-right corner
        br = np.array(piece["corners"][2], dtype=np.float32) * factor
        piece["x"] = round(float((br[0] - left + pad_x) / out.shape[1] * 100), 1)
        piece["y"] = round(float((br[1] - top + pad_y) / out.shape[0] * 100), 1)
    path = OUT_DIR / f"ua-room-{name}-v3.jpg"
    cv2.imwrite(str(path), out, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    return path


if __name__ == "__main__":
    rooms = json.loads((HERE / "rooms.json").read_text())
    for name in sys.argv[1:] or rooms:
        print(render(name, rooms[name]))
    (HERE / "rooms.json").write_text(json.dumps(rooms, indent=1, ensure_ascii=False))
