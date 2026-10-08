#!/usr/bin/env python3
"""Place a real artwork file onto the blank panel in an AI-generated room photo.

The room image is generated with an empty panel of the correct size on the wall.
This script finds that panel, warps the artwork onto it with the exact
perspective, and multiplies in the panel's own light and texture, so the
artwork pixels stay true while the room supplies light, shadow and material.

    python3 mockups/composite.py room.png artwork.png out.jpg
    python3 mockups/composite.py room.png artwork.png out.jpg --knockout-white
    python3 mockups/composite.py room.png artwork.png out.jpg --corners 410,520 1020,505 1030,960 405,975

--knockout-white lets the artwork's background colour (read from its border)
show the panel through, which is how a stencil sprayed onto LightBeton® looks. Without it the artwork
covers the panel completely (canvas or paper prints).
--debug writes <out>.debug.jpg with the detected panel outline.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

MIN_PANEL_AREA = 0.02          # panel must cover at least 2 % of the photo ...
MAX_PANEL_AREA = 0.6           # ... and at most 60 %
CANNY_THRESHOLDS = ((20, 60), (10, 30), (5, 20))
MAX_PANEL_STD = 30             # a blank panel is evenly coloured; busy regions are rejected
PANEL_INSET_PX = 3             # edge detection outlines the panel slightly outside its face
OCCLUDER_DARKNESS = 0.55       # pixels darker than 55 % of local panel light are objects in front
BORDER_SAMPLE_PX = 6           # artwork border width used to read its background colour
KNOCKOUT_NEAR = 6.0            # Lab distance from the background that is fully transparent ...
KNOCKOUT_FAR = 22.0            # ... and fully opaque
SHADING_STRENGTH = 0.85        # how much of the panel's light variation reaches the artwork


def order_corners(pts: np.ndarray) -> np.ndarray:
    """Return corners as top-left, top-right, bottom-right, bottom-left."""
    pts = pts.reshape(4, 2).astype(np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], dtype=np.float32)


def detect_panel(room: np.ndarray) -> np.ndarray:
    """Find the blank panel: the largest clean, evenly coloured quadrilateral.

    Panel edges against a white wall can be faint, so several edge thresholds are
    tried; the biggest uniform four-cornered shape wins (drawers and doors are
    smaller than a wall panel in these compositions).
    """
    gray = cv2.cvtColor(room, cv2.COLOR_BGR2GRAY)
    smooth = cv2.bilateralFilter(gray, 9, 40, 9)
    img_area = gray.size
    best, best_area = None, 0.0
    for low, high in CANNY_THRESHOLDS:
        edges = cv2.dilate(cv2.Canny(smooth, low, high), np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if not (MIN_PANEL_AREA * img_area < area < MAX_PANEL_AREA * img_area) or area <= best_area:
                continue
            approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
            if len(approx) != 4 or not cv2.isContourConvex(approx):
                continue
            quad = order_corners(approx)
            inside = np.zeros(gray.shape, np.uint8)
            cv2.fillConvexPoly(inside, quad.astype(np.int32), 255)
            if float(gray[inside > 0].std()) > MAX_PANEL_STD:
                continue
            best, best_area = quad, area
    if best is None:
        raise SystemExit("No blank panel found. Pass --corners x,y x,y x,y x,y (TL TR BR BL).")
    return shrink(best, PANEL_INSET_PX)


def shrink(quad: np.ndarray, px: float) -> np.ndarray:
    """Pull corners towards the centre so the dilated edge line is not included."""
    centre = quad.mean(axis=0)
    vec = centre - quad
    return quad + vec / np.linalg.norm(vec, axis=1, keepdims=True) * px


def panel_shading(room: np.ndarray, quad: np.ndarray, size: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Rectify the blank panel; return normalised light (incl. texture) and an occluder mask."""
    w, h = size
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    flat = cv2.warpPerspective(room, cv2.getPerspectiveTransform(quad, dst), (w, h)).astype(np.float32)
    lum = cv2.cvtColor(flat.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    broad = cv2.GaussianBlur(lum, (0, 0), sigmaX=w / 40)
    occluder = lum < broad * OCCLUDER_DARKNESS
    clean = np.where(occluder, broad, lum)
    shading = clean / max(np.percentile(clean, 95), 1.0)
    shading = 1.0 - SHADING_STRENGTH * (1.0 - shading)
    return shading, occluder


def knockout_alpha(art: np.ndarray) -> np.ndarray:
    """Opacity per pixel: the artwork's own background colour becomes transparent.

    The background is sampled from the artwork's border, so a light grey or cream
    ground knocks out as cleanly as pure white.
    """
    lab = cv2.cvtColor(art, cv2.COLOR_BGR2LAB).astype(np.float32)
    border = np.concatenate([lab[:BORDER_SAMPLE_PX].reshape(-1, 3), lab[-BORDER_SAMPLE_PX:].reshape(-1, 3),
                             lab[:, :BORDER_SAMPLE_PX].reshape(-1, 3), lab[:, -BORDER_SAMPLE_PX:].reshape(-1, 3)])
    background = np.median(border, axis=0)
    distance = np.linalg.norm(lab - background, axis=2)
    t = np.clip((distance - KNOCKOUT_NEAR) / (KNOCKOUT_FAR - KNOCKOUT_NEAR), 0, 1)
    return t * t * (3 - 2 * t)


def composite(room: np.ndarray, art: np.ndarray, quad: np.ndarray, knockout: bool) -> np.ndarray:
    top_w = np.linalg.norm(quad[1] - quad[0])
    left_h = np.linalg.norm(quad[3] - quad[0])
    size = (max(int(top_w), 64), max(int(left_h), 64))
    art = cv2.resize(art, size, interpolation=cv2.INTER_AREA).astype(np.float32)
    shading, occluder = panel_shading(room, quad, size)

    w, h = size
    src = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    rect = cv2.getPerspectiveTransform(quad, src)
    panel_flat = cv2.warpPerspective(room, rect, size).astype(np.float32)

    painted = art * shading[..., None]
    alpha = knockout_alpha(art.astype(np.uint8)) if knockout else np.ones(shading.shape, np.float32)
    alpha = np.where(occluder, 0.0, alpha)[..., None]
    flat_out = painted * alpha + panel_flat * (1 - alpha)

    back = cv2.getPerspectiveTransform(src, quad)
    out_h, out_w = room.shape[:2]
    warped = cv2.warpPerspective(flat_out, back, (out_w, out_h), flags=cv2.INTER_LANCZOS4)
    mask = cv2.warpPerspective(np.ones((h, w), np.float32), back, (out_w, out_h))
    mask = cv2.GaussianBlur(mask, (3, 3), 0)[..., None]
    return (warped * mask + room.astype(np.float32) * (1 - mask)).clip(0, 255).astype(np.uint8)


def parse_corners(values: list[str]) -> np.ndarray:
    if len(values) != 4:
        raise SystemExit("--corners needs four x,y pairs: TL TR BR BL")
    return np.array([[float(v) for v in p.split(",")] for p in values], dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("room", type=Path)
    ap.add_argument("artwork", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--corners", nargs=4, metavar="X,Y")
    ap.add_argument("--knockout-white", action="store_true")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    room = cv2.imread(str(args.room), cv2.IMREAD_COLOR)
    art = cv2.imread(str(args.artwork), cv2.IMREAD_COLOR)
    if room is None or art is None:
        sys.exit(f"Could not read {args.room if room is None else args.artwork}")

    quad = parse_corners(args.corners) if args.corners else detect_panel(room)
    out = composite(room, art, quad, args.knockout_white)
    cv2.imwrite(str(args.out), out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"wrote {args.out}  panel corners: " + " ".join(f"{x:.0f},{y:.0f}" for x, y in quad))

    if args.debug:
        dbg = room.copy()
        cv2.polylines(dbg, [quad.astype(np.int32)], True, (128, 0, 255), 4)
        cv2.imwrite(str(args.out.with_suffix(".debug.jpg")), dbg)


if __name__ == "__main__":
    main()
