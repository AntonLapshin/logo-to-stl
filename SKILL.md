---
name: logo-to-stl
description: Convert black-and-white logo image to flat print-ready STL via potrace + Blender extrude. Use when asked for logo STL, flat logo 3D print, black white image to STL, extrude PNG/JPEG to 2mm.
---

# Logo to STL (flat)

Black-and-white logo (`png/jpg/jpeg`, white background + black artwork) → vector → flat extruded STL, print-ready (base at Z=0).

Proven on: `logo.jpeg` (1024x1024, JPEG) → `dragon_logo_2mm.stl` (80 x 80 x 2mm, 0 non-manifold edges).

## Inputs

- `SRC`: logo image path (png/jpg/jpeg, black on white)
- `DST`: output STL path (default `<src-stem>_<height>mm.stl`)
- `SIZE`: largest XY dimension in mm (default 80)
- `HEIGHT`: extrusion height in mm (default 2)
- `THRESHOLD`: B/W cutoff 0-255 (default 128 single-file, 140 modular; use 128-150 for JPEG)

## Dependencies

- `potrace` on PATH (`potrace --version`)
- `blender` on PATH (tested 5.2.1 LTS, headless `--background` is fine)
- `uv` for Python deps (Pillow, numpy) — or system Pillow

## Workflow

### Option A — single file (quickstart)

```bash
uv run convert_logo_to_stl.py logo.png dragon_logo.stl --size 80 --height 2
```

Pipeline inside: PNG → threshold → PBM → `potrace -s --flat -t 2 --opttolerance 0.2 --alphamax 1.0 --turnpolicy minority` → Blender headless (import SVG, join, convert to mesh, scale XY, Solidify, export STL).

### Option B — modular (robust, recommended)

```bash
uv run scripts/logo_to_stl.py logo.jpeg dragon_logo_2mm.stl --size 80 --height 2 --threshold 140
```

What it does internally (see `scripts/`):

```bash
# threshold + median-filter + 2x upscale, save BMP (scripts/preprocess.py)
# potrace /tmp/logo.bmp -s -o /tmp/logo.svg --flat -t 2 --alphamax 1 --opttolerance 0.2 --turnpolicy minority
# blender --background --python scripts/blender_extrude.py -- --svg /tmp/logo.svg --out dragon_logo_2mm.stl --size 80 --height 2
```

Blender steps (`scripts/blender_extrude.py`):
1. Delete scene, `bpy.ops.import_curve.svg(filepath=svg)`
2. Select curves, join only if >1, set splines cyclic, `dimensions='2D'`, `fill_mode='BOTH'`
3. `bpy.ops.object.convert(target='MESH')`
4. Scale largest XY to `SIZE/1000`, `transform_apply`, `origin_set(BOUNDS)`, location `(0,0,0)`
5. Solidify: `thickness=HEIGHT/1000`, `offset=1.0`, `use_rim=True`, apply
6. EDIT: `remove_doubles(threshold=0.00001)`, `normals_make_consistent`
7. Export: `bpy.ops.wm.stl_export(filepath=out, export_selected_objects=True, apply_modifiers=True)`

### Verify (must pass before calling it done)

```bash
blender --background --python scripts/verify_stl.py -- --stl dragon_logo_2mm.stl
# expect: X≈SIZE, Z≈HEIGHT, nonmanifold=0
```

## Pitfalls

- Blender 5.x STL export arg is `export_selected_objects=True`, NOT `export_selected` (old) nor `bpy.ops.export_mesh.stl` (removed).
- Don't hand-roll PBM with numpy `packbits` — row padding is error-prone. Save BMP via Pillow (`mode='1'`) and let potrace read it (Option B does this).
- SVG from potrace for a connected logo is often a single `Curve` with many splines — don't `join` unconditionally; handle 1-object case (Option B does this).
- Keep base at Z=0 (`offset=1.0` + origin BOUNDS) so it slices sitting on the bed.
- JPEG logos need threshold tuning; 140 worked for the dragon, pure PNG may want 128.
