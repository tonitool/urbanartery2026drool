#!/usr/bin/env python3
"""Write the "Urban Artery Haus" into the room-tour section of a templates/index.json (pass the live copy)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETTINGS = {
    "heading": "Komm rein ins Urban Artery Haus.",
    "text": "Folge den Pfeilen durch Hof, Loft, Schlafzimmer, Bad, Atelier und Dach. Jede Nummer an der Wand ist ein Motiv in echter Größe, von S bis XL, im Hoch- oder Querformat. Tippe drauf und mach es zu deinem.",
    "make_label": "Make yours",
    "background": "#0C0C0C",
}


def haus_section() -> dict:
    haus = json.loads((HERE / "haus.json").read_text())
    blocks, order = {}, []
    for key, spec in haus.items():
        blocks[f"room-{key}"] = {"type": "room", "settings": {"name": spec["name"], "image": f"shopify://shop_images/ua-haus-{key}.jpg"}}
        order.append(f"room-{key}")
        for i, p in enumerate(spec["pieces"], 1):
            blocks[f"{key}-art-{i}"] = {"type": "piece", "settings": {
                "title": p["title"], "image": f"shopify://shop_images/ua-art-{p['art'].replace('.png', '.jpg')}",
                "size": p["size"], "format": p["format"], "x": round(p["x"]), "y": round(p["y"]),
                **({"product": p["product"]} if p.get("product") else {})}}
            order.append(f"{key}-art-{i}")
        for i, d in enumerate(spec["doors"], 1):
            blocks[f"{key}-door-{i}"] = {"type": "door", "settings": {
                "label": d["label"], "target": d["target"], "direction": d["direction"], "x": round(d["x"]), "y": round(d["y"])}}
            order.append(f"{key}-door-{i}")
    return {"type": "room-tour", "blocks": blocks, "block_order": order}


def main() -> None:
    home = json.loads(re.sub(r"^\s*/\*.*?\*/", "", Path(sys.argv[1]).read_text(), flags=re.S))
    old = home["sections"].get("room-tour", {})
    section = haus_section()
    section["settings"] = {**old.get("settings", {}), **SETTINGS}
    home["sections"]["room-tour"] = section
    print(json.dumps(home, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
