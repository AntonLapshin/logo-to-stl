import bpy
import sys

svg_path = sys.argv[sys.argv.index("--svg") + 1]
stl_path = sys.argv[sys.argv.index("--out") + 1]
size_mm = float(sys.argv[sys.argv.index("--size") + 1])
height_mm = float(sys.argv[sys.argv.index("--height") + 1])

size_m = size_mm / 1000.0
height_m = height_mm / 1000.0

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.import_curve.svg(filepath=svg_path)
curves = [o for o in bpy.context.scene.objects if o.type == 'CURVE']
print(f"curves={len(curves)}")
for c in curves:
    c.select_set(True)
bpy.context.view_layer.objects.active = curves[0]
if len(curves) > 1:
    bpy.ops.object.join()
logo = bpy.context.view_layer.objects.active

try:
    for s in logo.data.splines:
        s.use_cyclic_u = True
    logo.data.dimensions = '2D'
    logo.data.fill_mode = 'BOTH'
except Exception as e:
    print("fill setup:", e)

bpy.ops.object.convert(target='MESH')
logo = bpy.context.view_layer.objects.active

xs = [v.co.x for v in logo.data.vertices]
ys = [v.co.y for v in logo.data.vertices]
scale = size_m / max(max(xs) - min(xs), max(ys) - min(ys))
logo.scale = (scale, scale, 1.0)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
logo.location = (0, 0, 0)
bpy.context.view_layer.update()

mod = logo.modifiers.new("Solid", 'SOLIDIFY')
mod.thickness = height_m
mod.offset = 1.0
mod.use_rim = True
bpy.ops.object.modifier_apply(modifier=mod.name)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.remove_doubles(threshold=0.00001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

xs = [v.co.x for v in logo.data.vertices]
ys = [v.co.y for v in logo.data.vertices]
zs = [v.co.z for v in logo.data.vertices]
print(f"final mm X={(max(xs)-min(xs))*1000:.3f} Y={(max(ys)-min(ys))*1000:.3f} Z={(max(zs)-min(zs))*1000:.3f}")

bpy.ops.object.select_all(action='SELECT')
# Blender 5.x: export_selected_objects (not export_selected); export_mesh.stl is removed
bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True, apply_modifiers=True)
print("wrote", stl_path)
