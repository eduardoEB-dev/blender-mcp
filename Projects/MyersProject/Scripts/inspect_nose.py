import bpy, bmesh

OBJ_NAME = "michael_myers_mask"
obj = bpy.data.objects[OBJ_NAME]
me = obj.data

if me.is_editmode:
    bm = bmesh.from_edit_mesh(me)
else:
    bm = bmesh.new()
    bm.from_mesh(me)

bm.verts.ensure_lookup_table()

coords = [(v.co.x, v.co.y, v.co.z) for v in bm.verts]
xs = [c[0] for c in coords]
ys = [c[1] for c in coords]
zs = [c[2] for c in coords]

x_center = (min(xs) + max(xs)) / 2
z_total_min, z_total_max = min(zs), max(zs)

print(f"Full bbox  X:{min(xs):.3f}→{max(xs):.3f}  Y:{min(ys):.3f}→{max(ys):.3f}  Z:{min(zs):.3f}→{max(zs):.3f}")
print(f"X center: {x_center:.3f}")

# Nose = most-protruding (lowest Y) verts near X center, mid-Z
# Find top 200 most-protruding verts sorted by Y
sorted_by_y = sorted(bm.verts, key=lambda v: v.co.y)
print("\nTop 30 most-protruding verts (lowest Y):")
for v in sorted_by_y[:30]:
    print(f"  idx={v.index:5d}  X={v.co.x:.3f}  Y={v.co.y:.3f}  Z={v.co.z:.3f}")

# Find the single most-protruding vert near X center — that's the nose tip
nose_candidates = [v for v in bm.verts if abs(v.co.x - x_center) < 1.5]
nose_tip = min(nose_candidates, key=lambda v: v.co.y)
print(f"\nNose tip candidate: X={nose_tip.co.x:.3f}  Y={nose_tip.co.y:.3f}  Z={nose_tip.co.z:.3f}")

# Print verts within radius 2.0 of nose tip (the nose region)
nose_region = [v for v in bm.verts
               if abs(v.co.x - nose_tip.co.x) < 2.0
               and abs(v.co.z - nose_tip.co.z) < 2.0
               and v.co.y < nose_tip.co.y + 1.5]
print(f"\nNose region verts ({len(nose_region)} total):")
for v in sorted(nose_region, key=lambda v: v.co.y)[:40]:
    print(f"  X={v.co.x:.3f}  Y={v.co.y:.3f}  Z={v.co.z:.3f}")

if not me.is_editmode:
    bm.free()
