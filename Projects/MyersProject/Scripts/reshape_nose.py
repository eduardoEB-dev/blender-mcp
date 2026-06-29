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

# Locate nose tip: most-protruding vert near face X center
x_center = (min(v.co.x for v in bm.verts) + max(v.co.x for v in bm.verts)) / 2
nose_candidates = [v for v in bm.verts if abs(v.co.x - x_center) < 2.0]
nose_tip = min(nose_candidates, key=lambda v: v.co.y)
NT = nose_tip.co.copy()
print(f"Nose tip: X={NT.x:.3f}  Y={NT.y:.3f}  Z={NT.z:.3f}")

# ── Region bounds ──────────────────────────────────────────────────────────────
X_RADIUS = 1.9     # half-width of nose influence zone in X
Z_RADIUS = 1.6     # half-height influence zone in Z
Y_DEPTH  = 2.5     # how deep into the face (increasing Y) the effect fades

# ── Modification targets ───────────────────────────────────────────────────────
# 1. Narrow: compress X spread to 40% of current distance from nose center
X_NARROW_FACTOR = 0.40

# 2. Flatten bottom: raise verts below this Z toward FLAT_Z
#    Bottom of nose currently dips to ~6.26; flatten to just below nose tip
FLAT_Z      = NT.z - 0.15    # ≈ 6.54 — the new flat floor for the underside
FLAT_AMOUNT = 0.80            # move 80% of the way to FLAT_Z

modified = 0
for v in bm.verts:
    dx = v.co.x - NT.x
    dz = v.co.z - NT.z
    dy = v.co.y - NT.y   # 0 at tip surface, positive = deeper into head

    if abs(dx) > X_RADIUS or abs(dz) > Z_RADIUS or dy > Y_DEPTH or dy < 0:
        continue

    # Smooth falloff weights — cubic ease
    wx = max(0.0, 1.0 - (abs(dx) / X_RADIUS) ** 2)
    wz = max(0.0, 1.0 - (abs(dz) / Z_RADIUS) ** 2)
    wy = max(0.0, 1.0 - (dy / Y_DEPTH) ** 1.5)
    w  = wx * wz * wy

    if w < 0.001:
        continue

    # 1. Narrow X
    new_x = NT.x + dx * (1.0 - w * (1.0 - X_NARROW_FACTOR))
    v.co.x = new_x

    # 2. Flatten bottom — only verts below FLAT_Z, only on the underside (low Z area)
    if v.co.z < FLAT_Z:
        gap = FLAT_Z - v.co.z
        v.co.z += gap * FLAT_AMOUNT * w

    modified += 1

print(f"Modified {modified} verts")

# Recalculate normals
bm.normal_update()

if me.is_editmode:
    bmesh.update_edit_mesh(me)
else:
    bm.to_mesh(me)
    bm.free()

me.update()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("Saved.")
