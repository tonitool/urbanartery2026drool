#!/usr/bin/env python3
"""Merge the room tour and the sizes wall into a templates/index.json (pass the live copy)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOM_NAMES = {"wohnzimmer": "Wohnzimmer", "schlafzimmer": "Schlafzimmer", "bad": "Bad", "cafe": "Café", "buero": "Büro"}
DIMS = {"S": "20 × 30", "M": "40 × 60", "L": "80 × 120", "XL": "120 × 180"}


def room_tour() -> dict:
    rooms = json.loads((HERE / "rooms.json").read_text())
    blocks, order = {}, []
    for key, spec in rooms.items():
        blocks[f"room-{key}"] = {"type": "room", "settings": {"name": ROOM_NAMES[key], "image": f"shopify://shop_images/ua-room-{key}-v3.jpg"}}
        order.append(f"room-{key}")
        for i, p in enumerate(spec["pieces"], 1):
            bid = f"{key}-{i}"
            blocks[bid] = {"type": "piece", "settings": {
                "title": p["title"], "image": f"shopify://shop_images/ua-art-{p['art'].replace('.png', '.jpg')}",
                "size": p["size"], "format": p["format"], "x": round(p["x"]), "y": round(p["y"])}}
            order.append(bid)
    return {"type": "room-tour", "blocks": blocks, "block_order": order, "settings": {"background": "#0C0C0C"}}


def sizes_wall(old: dict, points: list[dict]) -> dict:
    blocks, order = {}, []
    for i, pt in enumerate(points, 1):
        dims = DIMS[pt["size"]]
        blocks[f"size-{i}"] = {"type": "point", "settings": {"label": f"{pt['size']} · {dims} cm", "x": round(pt["x"]), "y": round(pt["y"])}}
        order.append(f"size-{i}")
    settings = {**old.get("settings", {}), "image": "shopify://shop_images/ua-wall-sizes.jpg",
                "image_alt": "Vier Street-Art-Leinwände in S, M, L und XL an einer Wohnzimmerwand"}
    return {**old, "blocks": blocks, "block_order": order, "settings": settings}


def main() -> None:
    src, points_json = Path(sys.argv[1]), sys.argv[2]
    raw = re.sub(r"^\s*/\*.*?\*/", "", src.read_text(), flags=re.S)
    home = json.loads(raw)
    sections = home["sections"]
    sections["room-tour"] = room_tour()
    sections["shop-the-wall"] = sizes_wall(sections["shop-the-wall"], json.loads(points_json))
    order = [s for s in home["order"] if s != "room-tour"]
    order.insert(order.index("shop-the-wall"), "room-tour")
    home["order"] = order
    print(json.dumps(home, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
