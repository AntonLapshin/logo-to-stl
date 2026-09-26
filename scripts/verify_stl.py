import bpy
import sys
import bmesh

stl_path = sys.argv[sys.argv.index("--stl") + 1]

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.wm.stl_import(filepath=stl_path)
o = bpy.context.selected_objects[0]
xs = [v.co.x for v in o.data.vertices]
ys = [v.co.y for v in o.data.vertices]
zs = [v.co.z for v in o.data.vertices]
print(f"X {(max(xs)-min(xs))*1000:.3f}mm Y {(max(ys)-min(ys))*1000:.3f}mm Z {(max(zs)-min(zs))*1000:.3f}mm")
bpy.context.view_layer.objects.active = o
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(o.data)
nm = [e for e in bm.edges if not e.is_manifold]
print(f"edges={len(bm.edges)} nonmanifold={len(nm)} verts={len(bm.verts)} faces={len(bm.faces)}")
bpy.ops.object.mode_set(mode='OBJECT')
