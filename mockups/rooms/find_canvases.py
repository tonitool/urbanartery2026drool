#!/usr/bin/env python3
"""Find the blank canvases in a room render: each search box -> 4 corners (TL, TR, BR, BL)."""
import json
import sys

import cv2
import numpy as np


def order(pts: np.ndarray) -> list:
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return [pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]]


def find(img: np.ndarray, box: list) -> list:
    x0, y0, x1, y1 = box
    crop = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(contours, key=cv2.contourArea)
    quad = cv2.approxPolyDP(cv2.convexHull(c), 0.03 * cv2.arcLength(c, True), True).reshape(-1, 2)
    if len(quad) != 4:
        quad = cv2.boxPoints(cv2.minAreaRect(c))
    return [[int(p[0] + x0), int(p[1] + y0)] for p in order(np.array(quad, dtype=np.float32))]


if __name__ == "__main__":
    img = cv2.imread(sys.argv[1])
    boxes = json.loads(sys.argv[2])
    print(json.dumps([find(img, b) for b in boxes]))
