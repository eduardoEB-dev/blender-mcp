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
print(f"Original: {len(bm.verts)} verts  {len(bm.faces)} faces")

# Step 1: Solidify inward — negative = along inverted normals (into the head)
# 0.3 units ≈ 3mm if scene units are cm
THICKNESS = -0.3
bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=THICKNESS)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
print(f"After solidify: {len(bm.verts)} verts  {len(bm.faces)} faces")

# Step 2: Bisect at 65% of Y-depth — removes the back dome, keeps face + ears + sides
y_min = min(v.co.y for v in bm.verts)
y_max = max(v.co.y for v in bm.verts)
cut_y = y_min + (y_max - y_min) * 0.65
print(f"Y: {y_min:.3f} → {y_max:.3f}  |  cutting at Y={cut_y:.3f}")

bmesh.ops.bisect_plane(
    bm,
    geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
    plane_co=Vector((0.0, cut_y, 0.0)),
    plane_no=Vector((0.0, 1.0, 0.0)),
    clear_outer=True,   # remove high-Y (back of head)
    clear_inner=False,
)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
print(f"After bisect: {len(bm.verts)} verts  {len(bm.faces)} faces")

if me.is_editmode:
    bmesh.update_edit_mesh(me)
else:
    bm.to_mesh(me)
    bm.free()

me.update()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("Saved.")
