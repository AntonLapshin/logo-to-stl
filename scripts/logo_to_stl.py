#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["Pillow"]
# ///
"""One-shot: logo image -> flat STL. See ../SKILL.md.
Usage: uv run scripts/logo_to_stl.py SRC DST [--size 80] [--height 2] [--threshold 140]
Requires: potrace, blender on PATH.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from preprocess import image_to_bmp, bmp_to_svg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--size", type=float, default=80.0)
    ap.add_argument("--height", type=float, default=2.0)
    ap.add_argument("--threshold", type=int, default=140)
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as td:
        bmp = Path(td) / "logo.bmp"
        svg = Path(td) / "logo.svg"
        image_to_bmp(Path(a.src), bmp, a.threshold)
        bmp_to_svg(bmp, svg)
        cmd = ["blender", "--background", "--python", str(HERE / "blender_extrude.py"),
               "--", "--svg", str(svg), "--out", str(Path(a.dst).resolve()),
               "--size", str(a.size), "--height", str(a.height)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(r.stdout[-3000:])
        print(r.stderr[-1000:], file=sys.stderr)
        if not Path(a.dst).exists():
            raise SystemExit("Blender STL export failed")


if __name__ == "__main__":
    main()
