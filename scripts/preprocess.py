#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["Pillow"]
# ///
"""Preprocess B/W logo -> BMP -> potrace SVG. Called by logo_to_stl.py."""
import subprocess
from pathlib import Path
from PIL import Image, ImageFilter


def image_to_bmp(src: Path, dst_bmp: Path, threshold: int = 140, upscale: int = 2) -> None:
    im = Image.open(src)
    if "A" in im.getbands():
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im.convert("RGB"), mask=im.convert("RGBA").split()[3])
        im = bg
    gray = im.convert("L").filter(ImageFilter.MedianFilter(3))
    bw = gray.point(lambda v: 0 if v < threshold else 255, mode="1")
    if upscale != 1:
        bw = bw.resize((bw.width * upscale, bw.height * upscale), Image.NEAREST)
    bw.save(dst_bmp, format="BMP")
    print(f"BMP: {dst_bmp} {bw.size}")


def bmp_to_svg(bmp: Path, svg: Path) -> None:
    cmd = ["potrace", str(bmp), "-s", "-o", str(svg),
           "--flat", "-t", "2", "--alphamax", "1",
           "--opttolerance", "0.2", "--turnpolicy", "minority"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"potrace failed: {r.stderr}")
    print(f"SVG: {svg} ({svg.stat().st_size} bytes)")
