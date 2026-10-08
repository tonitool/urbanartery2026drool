#!/usr/bin/env python3
"""Render the preview's sample product images from the artworks in media/.

    python3 preview/make_demo.py

Writes preview/demo/demo-NN.jpg (product cards) and preview/demo/qv-NN-K.jpg
(quick-view slides: motif, room, close-up, second room, packshot) for each
sample product listed in DEMO below. Requires opencv-python and numpy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mockups"))
from place import card_crop, load_room, render  # noqa: E402


def save(image, path: Path) -> None:
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY, cv2.IMWRITE_JPEG_PROGRESSIVE, 1]):
        raise SystemExit(f"Could not write {path}")

OUT = ROOT / "preview" / "demo"
CARD_SIZE = (720, 960)
SLIDE_SIZE = (960, 1200)
JPEG_QUALITY = 78

# artwork file, knockout (stencil on concrete), card room/size, second room/size
DEMO = [
    ("ua-motiv-trane.jpg", False, ("wohnen-usm", "L"), ("essen", "L")),
    ("ua-motiv-whoa.jpg", True, ("wohnen-usm", "S"), ("flur", "M")),
    ("ua-motiv-por-favor.jpg", False, ("wohnen-usm", "L"), ("schlafen", "L")),
    ("ua-motiv-trane.jpg", False, ("wohnen-sofa", "XL"), ("arbeiten", "L")),
    ("ua-motiv-robot.jpg", False, ("essen", "L"), ("wohnen-sofa", "L")),
    ("ua-motiv-whoa.jpg", True, ("arbeiten", "L"), ("wohnen-usm", "M")),
    ("ua-motiv-por-favor.jpg", False, ("wohnen-sofa", "L"), ("flur", "L")),
    ("ua-motiv-robot.jpg", False, ("flur", "M"), ("wohnen-usm", "L")),
]


def fit(image, size):
    """Cover-crop to the target aspect ratio, then resize."""
    tw, th = size
    h, w = image.shape[:2]
    scale = max(tw / w, th / h)
    image = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    h, w = image.shape[:2]
    x, y = (w - tw) // 2, (h - th) // 2
    return image[y:y + th, x:x + tw]


def contain(image, size, background=(241, 241, 241)):
    """Letterbox the flat artwork on the image well colour."""
    tw, th = size
    h, w = image.shape[:2]
    scale = min(tw / w, th / h) * 0.82
    art = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    canvas = cv2.copyMakeBorder(art, 0, 0, 0, 0, cv2.BORDER_CONSTANT)
    out = cv2.resize(canvas[:1, :1], size)
    out[:] = background
    y, x = (th - art.shape[0]) // 2, (tw - art.shape[1]) // 2
    out[y:y + art.shape[0], x:x + art.shape[1]] = art
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    manifest = []
    for i, (art_file, knockout, (room_a, size_a), (room_b, size_b)) in enumerate(DEMO, 1):
        art = cv2.imread(str(ROOT / "media" / art_file))
        cfg_a, img_a = load_room(room_a)
        cfg_b, img_b = load_room(room_b)
        room1 = render(img_a, cfg_a, size_a, "quer", art, knockout)
        room2 = render(img_b, cfg_b, size_b, "quer", art, knockout)
        save(cv2.resize(card_crop(room1, cfg_a, size_a, "quer"), CARD_SIZE, interpolation=cv2.INTER_AREA), OUT / f"demo-{i:02d}.jpg")
        slides = [
            ("Motiv", contain(art, SLIDE_SIZE)),
            (f"{size_a} im Raum", fit(room1, SLIDE_SIZE)),
            ("Nahaufnahme", fit(card_crop(room1, cfg_a, size_a, "quer", ratio=4 / 5), SLIDE_SIZE)),
            (f"{size_b} im Raum", fit(room2, SLIDE_SIZE)),
        ]
        names = []
        for k, (label, image) in enumerate(slides, 1):
            name = f"qv-{i:02d}-{k}.jpg"
            save(image, OUT / name)
            names.append({"file": name, "label": label})
        manifest.append({"art": art_file, "slides": names})
        print(f"demo {i:02d}: {art_file} ({room_a} {size_a}, {room_b} {size_b})")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
