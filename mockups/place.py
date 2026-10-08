#!/usr/bin/env python3
"""Render an exact-size Urban Artery piece into a calibrated empty-wall room photo.

Image models cannot hold absolute sizes, so the panel is drawn here instead:
each room in rooms.json is calibrated once (pixels per cm from a furniture piece
of known width, plus where art hangs), and the panel is placed at true scale with
the LightBeton® texture, a soft wall shadow and the room's own light falloff.

    python3 mockups/place.py wohnen-usm L quer artwork.png out.jpg
    python3 mockups/place.py wohnen-usm S hoch stencil.png out.jpg --knockout-white
    python3 mockups/place.py wohnen-usm M quer --blank out.jpg      # empty panel, to check placement
    python3 mockups/place.py wohnen-usm L quer artwork.png card.jpg --card   # tight crop for product cards
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from composite import knockout_alpha  # noqa: E402

HERE = Path(__file__).resolve().parent
SIZES_CM = {"S": (20, 30), "M": (40, 60), "L": (80, 120), "XL": (120, 180)}  # portrait w × h
PANEL_DEPTH_CM = 1.5          # LightBeton panels stand slightly off the wall
SHADOW_OFFSET_CM = (1.2, 1.8)  # daylight from the left: shadow falls right and down
SHADOW_BLUR_CM = 2.0
SHADOW_OPACITY = 0.30
OCCLUDER_THRESHOLD = 22        # colour distance from the modelled bare wall that marks an object in front
SHADOW_CHROMA_MAX = 4.0        # Lab a/b shift below which a darker pixel is a shadow, not an object
SHADOW_TEXTURE_MAX = 6.0       # ... and only if it is smooth (objects have texture and edges)
WALL_FIT_ROUNDS = 3            # robust refits of the wall model (objects are dropped as outliers)
ART_SHADING_STRENGTH = 0.85
MAX_SILENT_CROP = 0.05         # crop more than this and place.py warns (wrong orientation for the artwork)
CARD_FILL = {"S": 0.34, "M": 0.44, "L": 0.62, "XL": 0.66}  # share of the card width the piece takes
CARD_TOP_SHARE = 0.38          # how much of the free height goes above the piece (rest shows furniture)


def load_room(name: str) -> tuple[dict, np.ndarray]:
    rooms = json.loads((HERE / "rooms.json").read_text())
    if name not in rooms:
        raise SystemExit(f"Unknown room '{name}'. Known: {', '.join(rooms)}")
    cfg = rooms[name]
    image = cv2.imread(str(HERE / cfg["file"]), cv2.IMREAD_COLOR)
    if image is None:
        raise SystemExit(f"Cannot read {cfg['file']}")
    return cfg, image


def panel_rect(cfg: dict, size: str, orientation: str) -> tuple[int, int, int, int]:
    """Return x, y, w, h in pixels for the panel, from the room calibration."""
    x1, x2 = cfg["ref_px"]
    px_per_cm = abs(x2 - x1) / cfg["ref_cm"]
    w_cm, h_cm = SIZES_CM[size]
    if orientation == "quer":
        w_cm, h_cm = h_cm, w_cm
    w, h = round(w_cm * px_per_cm), round(h_cm * px_per_cm)

    mode = cfg.get("mode", {}).get(size, "hang")
    if mode == "lean":
        bottom = cfg["surface_y"]
        cx = cfg.get("lean_x", cfg["center_x"])
    else:
        bottom = cfg["surface_y"] - round(cfg.get("gap_cm", 22) * px_per_cm)
        cx = cfg["center_x"]
    return round(cx - w / 2), bottom - h, w, h


def occluder_mask(room: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    """Soft 0–1 mask of objects in front of the wall inside the panel rectangle.

    The bare wall is modelled as a smooth quadratic colour field fitted to the
    panel area plus a margin, refitted after dropping outliers (the objects).
    Pixels far from that model are objects; a 1 px feather avoids jagged edges.
    """
    H, W = room.shape[:2]
    m = max(8, round(0.15 * max(w, h)))
    x0, y0, x1, y1 = max(0, x - m), max(0, y - m), min(W, x + w + m), min(H, y + h + m)
    region = cv2.cvtColor(room[y0:y1, x0:x1], cv2.COLOR_BGR2LAB).astype(np.float32)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    xn, yn = (xx - x0) / max(x1 - x0, 1), (yy - y0) / max(y1 - y0, 1)
    design = np.stack([np.ones_like(xn), xn, yn, xn * xn, yn * yn, xn * yn], -1).reshape(-1, 6)
    pixels = region.reshape(-1, 3)
    inlier = np.ones(len(pixels), bool)
    for _ in range(WALL_FIT_ROUNDS):
        coef, *_ = np.linalg.lstsq(design[inlier], pixels[inlier], rcond=None)
        resid = np.linalg.norm(pixels - design @ coef, axis=1)
        inlier = resid < max(np.percentile(resid[inlier], 70) * 2.5, 6.0)
    diff = (pixels - design @ coef).reshape(region.shape)
    distance = resid.reshape(region.shape[:2])
    # Shadows cast on the wall only darken it: same hue, smooth. They sit behind the
    # panel, so they must not count as objects in front of it.
    chroma_shift = np.hypot(diff[..., 1], diff[..., 2])
    gray = region[..., 0]
    texture = np.abs(cv2.Laplacian(cv2.GaussianBlur(gray, (3, 3), 0), cv2.CV_32F))
    shadow = (diff[..., 0] < 0) & (chroma_shift < SHADOW_CHROMA_MAX) & (texture < SHADOW_TEXTURE_MAX)
    hard = ((distance > OCCLUDER_THRESHOLD) & ~shadow).astype(np.uint8)
    hard = cv2.morphologyEx(hard, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    soft = cv2.GaussianBlur(hard.astype(np.float32), (3, 3), 0)
    return soft[y - y0:y - y0 + h, x - x0:x - x0 + w]


def wall_light(room: np.ndarray) -> np.ndarray:
    """Smooth luminance of the room, used to light the panel like the wall around it."""
    gray = cv2.cvtColor(room, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return cv2.GaussianBlur(gray, (0, 0), sigmaX=room.shape[1] / 25)


def cover(art: np.ndarray, w: int, h: int) -> np.ndarray:
    """Fit the artwork to the panel without distorting it: centre-crop to the panel's ratio.

    A portrait panel with a landscape artwork (or the reverse) loses its sides, so
    pick the orientation that matches the artwork; a warning is printed when the
    crop removes more than 5 % of either dimension.
    """
    ah, aw = art.shape[:2]
    target, source = w / h, aw / ah
    if source > target:
        new_w = round(ah * target)
        x = (aw - new_w) // 2
        art, lost = art[:, x:x + new_w], 1 - new_w / aw
    else:
        new_h = round(aw / target)
        y = (ah - new_h) // 2
        art, lost = art[y:y + new_h], 1 - new_h / ah
    if lost > MAX_SILENT_CROP:
        print(f"warning: artwork cropped by {lost:.0%} to fit a {w}×{h} panel; "
              "use the orientation that matches the artwork", file=sys.stderr)
    return cv2.resize(art, (w, h), interpolation=cv2.INTER_AREA)


def make_face(w: int, h: int, art: np.ndarray | None, knockout: bool) -> np.ndarray:
    tex = cv2.imread(str(HERE / "textures" / "lightbeton.jpg"), cv2.IMREAD_COLOR)
    tex = cv2.resize(tex, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
    if art is None:
        return tex
    art = cover(art, w, h).astype(np.float32)
    lum = cv2.cvtColor(tex.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    shading = 1.0 - ART_SHADING_STRENGTH * (1.0 - lum / max(np.percentile(lum, 95), 1.0))
    painted = art * shading[..., None]
    alpha = knockout_alpha(art.astype(np.uint8)) if knockout else np.ones((h, w), np.float32)
    return painted * alpha[..., None] + tex * (1 - alpha[..., None])


def render(room: np.ndarray, cfg: dict, size: str, orientation: str,
           art: np.ndarray | None, knockout: bool) -> np.ndarray:
    x, y, w, h = panel_rect(cfg, size, orientation)
    H, W = room.shape[:2]
    if x < 0 or y < 0 or x + w > W or y + h > H:
        raise SystemExit(f"{size} {orientation} does not fit this room photo ({x},{y},{w}×{h}).")
    px_per_cm = abs(cfg["ref_px"][1] - cfg["ref_px"][0]) / cfg["ref_cm"]
    out = room.astype(np.float32)

    # Objects in front of the wall (vase, branch, lamp) inside the panel area stay in front.
    occluder = occluder_mask(room, x, y, w, h)

    # Soft shadow on the wall.
    shadow = np.zeros((H, W), np.float32)
    dx, dy = (round(v * px_per_cm) for v in SHADOW_OFFSET_CM)
    cv2.rectangle(shadow, (x + dx, y + dy), (x + w + dx, y + h + dy), 1.0, -1)
    shadow = cv2.GaussianBlur(shadow, (0, 0), sigmaX=max(SHADOW_BLUR_CM * px_per_cm, 1))
    out *= (1 - SHADOW_OPACITY * shadow)[..., None]

    # Panel face, lit like the wall at that spot.
    light = wall_light(room)
    region_light = light[y:y + h, x:x + w]
    face = make_face(w, h, art, knockout) * (region_light / np.percentile(light, 90))[..., None]
    # Hairline edge so the slab reads as a physical object.
    edge = max(1, round(0.25 * px_per_cm))
    face[:, -edge:] *= 0.86
    face[-edge:, :] *= 0.82
    face[:edge, :] *= 1.04

    keep = occluder[..., None]
    out[y:y + h, x:x + w] = keep * room[y:y + h, x:x + w].astype(np.float32) + (1 - keep) * face
    return out.clip(0, 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("room")
    ap.add_argument("size", choices=SIZES_CM)
    ap.add_argument("orientation", choices=("hoch", "quer"))
    ap.add_argument("artwork", nargs="?", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--knockout-white", action="store_true")
    ap.add_argument("--blank", action="store_true", help="render the empty panel only")
    ap.add_argument("--card", action="store_true", help="tight 3:4 crop around the piece for product cards")
    args = ap.parse_args()

    cfg, room = load_room(args.room)
    art = None
    if not args.blank:
        if args.artwork is None:
            raise SystemExit("Give an artwork file or --blank.")
        art = cv2.imread(str(args.artwork), cv2.IMREAD_COLOR)
        if art is None:
            raise SystemExit(f"Cannot read {args.artwork}")
    out = render(room, cfg, args.size, args.orientation, art, args.knockout_white)
    if args.card:
        out = card_crop(out, cfg, args.size, args.orientation)
    save(out, args.out)
    print(f"wrote {args.out}")


def card_crop(image: np.ndarray, cfg: dict, size: str, orientation: str, ratio: float = 3 / 4) -> np.ndarray:
    """Tight 3:4 crop around the piece with some furniture below, for product cards.

    The crop is sized so the artwork fills about half the frame width (more for
    small pieces), which keeps it readable in a 300 px card while still showing
    scale against the furniture.
    """
    x, y, w, h = panel_rect(cfg, size, orientation)
    H, W = image.shape[:2]
    crop_w = max(w / CARD_FILL[size], h / CARD_FILL[size] * ratio)
    crop_w = min(crop_w, W, H * ratio)
    crop_h = crop_w / ratio
    cx = x + w / 2
    top = y - (crop_h - h) * CARD_TOP_SHARE
    left = min(max(cx - crop_w / 2, 0), W - crop_w)
    top = min(max(top, 0), H - crop_h)
    return image[round(top):round(top + crop_h), round(left):round(left + crop_w)]


def save(image: np.ndarray, path: Path) -> None:
    params = [cv2.IMWRITE_JPEG_QUALITY, 90] if path.suffix.lower() in (".jpg", ".jpeg") else []
    if not cv2.imwrite(str(path), image, params):
        raise SystemExit(f"Could not write {path}")


if __name__ == "__main__":
    main()
