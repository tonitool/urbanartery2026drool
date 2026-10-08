#!/usr/bin/env python3
"""Prompts for the room-plate library.

Image models do not respect absolute sizes (a "20 × 30 cm" panel comes out
40–50 cm wide), so the library is built from EMPTY walls: each room is generated
once without art, calibrated against a furniture piece of known width, and
mockups/place.py draws the panel at the exact size.

    python3 mockups/room_prompts.py            # print the empty-room prompts as JSON
    python3 mockups/room_prompts.py --list     # just the room names
"""
from __future__ import annotations

import json
import sys

BASE = (
    "Candid smartphone photo, perfectly frontal eye-level view, the back wall parallel to the camera. "
    "Renovated Hamburg Altbau "
    "apartment: herringbone oak parquet, white walls, subtle ceiling stucco, soft overcast daylight "
    "from a window on the left. Scandinavian minimal interior with designer furniture, warm neutral "
    "tones, uncluttered. {room} {wall} No people, no text, no logos, natural colours, realistic UGC "
    "look, slight phone-camera grain."
)

WALL = (
    "The wall above it is completely empty plain white wall with generous free space: no art, no "
    "pictures, no frames, no mirrors, no shelves on it."
)

ROOMS = {
    "wohnen-usm": {
        "room": "A white USM Haller sideboard, two modules wide (153 cm wide, 74 cm high) with chrome "
                "tubes, a stoneware vase with a dried branch and two art books on top.",
        "placement": {
            "S": "leaning against the wall on top of the sideboard next to the vase",
            "M": "hung centred on the wall above the sideboard",
            "L": "hung centred on the wall above the sideboard",
            "XL": "hung centred on the wall above the sideboard, clearly wider than half the sideboard",
        },
    },
    "wohnen-sofa": {
        "room": "A low three-seat sofa in oat-coloured linen (230 cm wide), an Artek stool as side "
                "table with a ceramic cup, a wool throw.",
        "placement": {
            "S": "standing on the Artek stool beside the sofa, leaning against the wall",
            "M": "hung on the wall above the sofa, slightly off-centre",
            "L": "hung centred on the wall above the sofa",
            "XL": "hung centred on the wall above the sofa",
        },
    },
    "essen": {
        "room": "A solid oak dining table (200 cm long) with four black Thonet bentwood chairs, a "
                "white glass globe pendant above, a narrow oak sideboard against the back wall.",
        "placement": {
            "S": "leaning against the wall on the narrow oak sideboard",
            "M": "hung on the wall behind the dining table",
            "L": "hung on the wall behind the dining table",
            "XL": "hung on the wall behind the dining table",
        },
    },
    "schlafen": {
        "room": "A bed 160 cm wide with rumpled oat and white linen bedding, two small oak nightstands "
                "with a ceramic lamp.",
        "placement": {
            "S": "leaning against the wall on the left nightstand",
            "M": "hung centred on the wall above the bed",
            "L": "hung centred on the wall above the bed",
            "XL": "standing on the floor leaning against the wall beside the bed",
        },
    },
    "flur": {
        "room": "A bright Altbau hallway with a tall white panelled double door at the side, a slim "
                "oak bench (120 cm) with a folded wool blanket, a single coat hook.",
        "placement": {
            "S": "leaning against the wall on the oak bench",
            "M": "hung on the wall above the oak bench",
            "L": "hung on the wall above the oak bench",
            "XL": "standing on the floor leaning against the wall next to the bench",
        },
    },
    "arbeiten": {
        "room": "A white USM Haller desk (175 cm wide), a Vitra Eames aluminium office chair, a closed "
                "laptop and a ceramic cup on the desk, a tall plant at the far right edge.",
        "placement": {
            "S": "leaning against the wall on the desk",
            "M": "hung on the wall above the desk",
            "L": "hung on the wall above the desk",
            "XL": "hung on the wall beside the desk",
        },
    },
}


def plates() -> list[dict]:
    return [
        {"name": name, "prompt": BASE.format(room=room["room"], wall=WALL)}
        for name, room in ROOMS.items()
    ]


if __name__ == "__main__":
    items = plates()
    if "--list" in sys.argv:
        print("\n".join(p["name"] for p in items))
    else:
        print(json.dumps(items, ensure_ascii=False, indent=2))
