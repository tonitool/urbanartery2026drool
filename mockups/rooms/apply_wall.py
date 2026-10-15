#!/usr/bin/env python3
"""Put the long sizes wall into the shop-the-wall section of a templates/index.json (pass the live copy)."""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIMS = {"S": (20, 30), "M": (40, 60), "L": (80, 120), "XL": (120, 180)}

home = json.loads(re.sub(r"^\s*/\*.*?\*/", "", Path(sys.argv[1]).read_text(), flags=re.S))
spec = json.loads((HERE / "wall.json").read_text())
points = json.loads(subprocess.check_output([sys.executable, str(HERE / "render_wall.py")], text=True).strip().splitlines()[-1])
blocks, order = {}, []
for i, p in enumerate(points, 1):
    w, h = DIMS[p["size"]]
    if p["format"] == "Querformat":
        w, h = h, w
    blocks[f"size-{i}"] = {"type": "point", "settings": {"label": f"{p['size']} · {w} × {h} cm · {p['format']}", "x": round(p["x"]), "y": round(p["y"])}}
    order.append(f"size-{i}")
section = home["sections"]["shop-the-wall"]
section["blocks"], section["block_order"] = blocks, order
section["settings"] = {**section.get("settings", {}), "image": f"shopify://shop_images/{spec['out']}", "fit_desktop": False,
                       "image_alt": "Acht Street-Art-Leinwände in S, M, L und XL, hoch und quer, an einer langen Wohnzimmerwand"}
print(json.dumps(home, ensure_ascii=False, indent=2))
