import bpy, bmesh
from mathutils import Vector

OBJ_NAME = "michael_myers_mask"
obj = bpy.data.objects[OBJ_NAME]
me = obj.data

if me.is_editmode:
    bm = bmesh.from_edit_mesh(me)
else:
    bm = bmesh.new()
    bm.from_mesh(me)

bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()

coords = [v.co for v in bm.verts]
xs = [v.x for v in coords]; ys = [v.y for v in coords]; zs = [v.z for v in coords]
print(f"Verts: {len(bm.verts)}  Faces: {len(bm.faces)}")
print(f"X: {min(xs):.3f} → {max(xs):.3f}")
print(f"Y: {min(ys):.3f} → {max(ys):.3f}")
print(f"Z: {min(zs):.3f} → {max(zs):.3f}")

# Sample face normals to understand orientation
normals = [f.normal for f in bm.faces]
avg_nx = sum(n.x for n in normals) / len(normals)
avg_ny = sum(n.y for n in normals) / len(normals)
avg_nz = sum(n.z for n in normals) / len(normals)
print(f"Avg face normal: ({avg_nx:.3f}, {avg_ny:.3f}, {avg_nz:.3f})")
print("(normals pointing toward +Y = face facing forward/outward)")

if not me.is_editmode:
    bm.free()
