# logo-to-stl

Black-and-white logo image → flat print-ready STL (base at Z=0, watertight).

Pipeline: PNG/JPG → threshold → `potrace` SVG → headless Blender extrude → STL.

## Requires

- `potrace`, `blender` on PATH
- `uv` (pulls Pillow, numpy automatically)

## Usage

Single file:

```bash
uv run convert_logo_to_stl.py logo.png out.stl --size 80 --height 2 --threshold 128
```

Robust modular version (median-filter, BMP instead of hand-rolled PBM, Blender 5.x API fix):

```bash
uv run scripts/logo_to_stl.py logo.jpeg out.stl --size 80 --height 2 --threshold 140
```

Verify:

```bash
blender --background --python scripts/verify_stl.py -- --stl out.stl
```

## Options

| Flag | Default | Meaning |
|---|---|---|
| `--size` | 80 | largest XY dimension, mm |
| `--height` | 2 | extrusion height, mm |
| `--threshold` | 128 / 140 | B/W cutoff (try 128–150 for JPEG) |

## Layout

- `convert_logo_to_stl.py` — single-file quickstart
- `scripts/logo_to_stl.py`, `preprocess.py`, `blender_extrude.py`, `verify_stl.py` — modular version
- `SKILL.md` — agent skill definition

MIT.
