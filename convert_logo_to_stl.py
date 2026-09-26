#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["Pillow", "numpy"]
# ///
"""Convert black&white logo PNG to print-ready STL, flat 2mm height.
Usage: uv run convert_logo_to_stl.py logo.png dragon_logo.stl [--size 80] [--height 2]
Pipeline: PNG -> threshold -> PBM -> potrace (SVG) -> Blender (extrude + export STL)
Requires: potrace, blender on PATH
"""
import subprocess, sys, os, tempfile
from pathlib import Path

def png_to_svg(src_png: Path, dst_svg: Path, threshold: int = 128):
    from PIL import Image
    import numpy as np
    img = Image.open(src_png).convert("RGB")
    # flatten alpha on white if present
    if "A" in Image.open(src_png).getbands():
        bg = Image.new("RGB", img.size, (255,255,255))
        a = Image.open(src_png).convert("RGBA").split()[3]
        bg.paste(img, mask=a)
        img = bg
    gray = img.convert("L")
    arr = np.array(gray)
    h, w = arr.shape
    # PBM P4 spec: 1=black, 0=white. potrace traces 1 (black) as foreground.
    # Logo black (arr<threshold) must become 1 in PBM.
    pbm_data = (arr < threshold).astype(np.uint8)  # logo black=1, background white=0
    with tempfile.NamedTemporaryFile(suffix=".pbm", delete=False) as f:
        pbm_path = f.name
    with open(pbm_path, "wb") as f:
        f.write(f"P4\n{w} {h}\n".encode())
        f.write(bytearray(((pbm_data.reshape(h, w) ).tolist() and __import__('numpy').packbits(pbm_data, axis=1).tobytes())))
    # potrace to svg
    cmd = ["potrace", pbm_path, "-s", "-o", str(dst_svg), "--flat", "-t", "2", "--opttolerance", "0.2", "--alphamax", "1.0", "--turnpolicy", "minority"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(pbm_path)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise SystemExit("potrace failed")
    print(f"SVG written: {dst_svg}")

BLENDER_SCRIPT = r'''
import bpy, sys, os, math
svg_path = sys.argv[sys.argv.index("--svg") + 1]
stl_path = sys.argv[sys.argv.index("--out") + 1]
size_mm = float(sys.argv[sys.argv.index("--size") + 1])
height_mm = float(sys.argv[sys.argv.index("--height") + 1])

# clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# import svg
bpy.ops.import_curve.svg(filepath=svg_path)
curves = [o for o in bpy.context.scene.objects if o.type == 'CURVE']
print(f"imported {len(curves)} curves")
for c in curves:
    c.select_set(True)
    bpy.context.view_layer.objects.active = c
# join into one
bpy.ops.object.join()
logo = bpy.context.view_layer.objects.active
logo.name = "DragonLogo"

# convert to mesh
bpy.ops.object.convert(target='MESH')
# join disconnected? keep as-is, remove doubles, recalc
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

# normalize scale: fit largest XY dim to size_mm
import mathutils
verts = [v.co for v in logo.data.vertices]
xs = [v.x for v in verts]; ys = [v.y for v in verts]
dx = max(xs)-min(xs); dy = max(ys)-min(ys)
cur_size = max(dx, dy)
scale = (size_mm/1000.0) / cur_size
logo.scale = (scale, scale, 1.0)
bpy.ops.object.transform_apply(scale=True)

# center XY, put min Z at 0
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
logo.location = (0,0,0)

# extrude flat: solidify modifier
mod = logo.modifiers.new("Solid", 'SOLIDIFY')
mod.thickness = height_mm/1000.0
mod.offset = 1.0  # extrude upward from 0
mod.use_rim = True
bpy.context.view_layer.objects.active = logo
bpy.ops.object.modifier_apply(modifier=mod.name)

# ensure exact height + base at Z=0 (corrects any Solidify offset doubling)
verts = [v.co for v in logo.data.vertices]
zs = [v.z for v in verts]
dz = max(zs)-min(zs) if zs else 0
if dz > 1e-9:
    zscale = (height_mm/1000.0) / dz
    logo.scale = (1.0, 1.0, zscale)
    bpy.ops.object.transform_apply(scale=True)
    # shift so min Z = 0
    min_z = min(v.co.z for v in logo.data.vertices)
    logo.location.z -= min_z
    bpy.ops.object.transform_apply(location=True)

# ensure manifold-ish: merge doubles again + recalc normals
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.remove_doubles(threshold=0.00001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

# export STL (Blender 5.x API: filepath + check_existing)
try:
    bpy.ops.wm.stl_export(filepath=stl_path, check_existing=False, export_selected_objects=False, apply_modifiers=True)
except Exception as e:
    print("stl_export failed, trying mesh.stl:", e)
    bpy.ops.export_mesh.stl(filepath=stl_path)

print(f"STL written: {stl_path}")
'''

def svg_to_stl(svg: Path, stl: Path, size_mm=80.0, height_mm=2.0):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(BLENDER_SCRIPT)
        script = f.name
    cmd = ["blender", "--background", "--python", script, "--", "--svg", str(svg), "--out", str(stl), "--size", str(size_mm), "--height", str(height_mm)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout[-4000:])
    print(r.stderr[-2000:], file=sys.stderr)
    os.unlink(script)
    if not stl.exists():
        raise SystemExit("Blender STL export failed")
    print(f"Done: {stl} ({stl.stat().st_size} bytes)")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="logo.png / jpg")
    ap.add_argument("output", nargs="?", default="dragon_logo_2mm.stl")
    ap.add_argument("--size", type=float, default=80.0, help="largest XY dimension in mm")
    ap.add_argument("--height", type=float, default=2.0, help="extrusion height in mm")
    ap.add_argument("--threshold", type=int, default=128)
    a = ap.parse_args()
    src = Path(a.input); stl = Path(a.output)
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        svg = Path(f.name)
    png_to_svg(src, svg, a.threshold)
    svg_to_stl(svg, stl, a.size, a.height)
    os.unlink(svg)
