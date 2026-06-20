"""
Replace 30 cylindrical grip channels with rocket-shaped indentations.
Fins: swept-back triangles (outward + downward) — Star Command badge style.

Channel geometry:
  - 30 channels at 12-deg intervals, starting at 0 deg
  - Zone Z 40-76mm, cup center (43.94, 44.45), outer radius 43.94mm
  - Existing channel depth ~1mm

Rocket profile (11-vertex closed polygon):
  - Nose:  pointed V, 6mm tall at top
  - Body:  narrow 2.0mm wide (1.0mm half-width)
  - Fins:  swept-back right-triangles, leading edge sweeps out+down
           top attach Z=56, outer tip at (±3.0, Z=42)
  - Exhaust: narrow 2.0mm, Z 38-42
  Cutter depth: 1.7mm (outer 44.7 -> inner 42.2)
"""

import bpy, bmesh, math, os, shutil

# ── Parameters ─────────────────────────────────────────────────────────────
CUP_NAME  = 'EFCooler_Cup'
CX, CY    = 43.94, 44.45
N_ROCKETS = 30

R_OUTER = 44.7
R_INNER = 42.2

BODY_HW  = 1.0    # half-width of body / exhaust
FIN_HW   = 3.0    # half-width at fin outer tip
NOSE_H   = 6.0    # nose cone height

# Z positions (channel exists Z 40-76; cutter slightly larger)
Z_MAX     = 77.0   # nose tip (1mm above channel cap)
Z_NS      = 71.0   # nose shoulder (Z_MAX - NOSE_H)
Z_FIN_TOP = 56.0   # where fin's leading edge leaves the body
Z_FIN_TIP = 42.0   # fin outer tip Z (swept down to here)
Z_MIN     = 38.0   # exhaust base (2mm below channel bottom)

BLEND_PATH  = r"d:\Blender\RocketCup.blend"
BACKUP_PATH = r"d:\Blender\RocketCup_backup.blend"

# ── Restore from backup ─────────────────────────────────────────────────────
print("Restoring from backup...")
bpy.ops.wm.open_mainfile(filepath=BACKUP_PATH)
print("Backup loaded.")

# ── Rocket profile: 11 vertices ─────────────────────────────────────────────
#
#      (0, Z_MAX)            ← nose tip
#     (-1, Z_NS)             ← L nose shoulder
#     (-1, Z_FIN_TOP)        ← L body at fin leading-edge start
#     (-3, Z_FIN_TIP)        ← L fin outer tip  (swept outward + downward)
#     (-1, Z_FIN_TIP)        ← L body below fin
#     (-1, Z_MIN)            ← L exhaust base
#      (1, Z_MIN)            ← R exhaust base
#      (1, Z_FIN_TIP)        ← R body below fin
#      (3, Z_FIN_TIP)        ← R fin outer tip
#      (1, Z_FIN_TOP)        ← R body at fin leading-edge start
#      (1, Z_NS)             ← R nose shoulder
#
profile = [
    ( 0.0,    Z_MAX),       # 0  nose tip
    (-BODY_HW, Z_NS),       # 1  L nose shoulder
    (-BODY_HW, Z_FIN_TOP),  # 2  L body at fin top
    (-FIN_HW,  Z_FIN_TIP),  # 3  L fin outer tip  (swept out + down)
    (-BODY_HW, Z_FIN_TIP),  # 4  L body below fin
    (-BODY_HW, Z_MIN),      # 5  L exhaust base
    ( BODY_HW, Z_MIN),      # 6  R exhaust base
    ( BODY_HW, Z_FIN_TIP),  # 7  R body below fin
    ( FIN_HW,  Z_FIN_TIP),  # 8  R fin outer tip
    ( BODY_HW, Z_FIN_TOP),  # 9  R body at fin top
    ( BODY_HW, Z_NS),       # 10 R nose shoulder
]
NP = len(profile)   # 11

print("Building %d rocket cutter meshes (NP=%d)..." % (N_ROCKETS, NP))

bm = bmesh.new()
for i in range(N_ROCKETS):
    theta     = math.radians(i * 360.0 / N_ROCKETS)
    cos_t     = math.cos(theta)
    sin_t     = math.sin(theta)

    ov, iv = [], []
    for (tang, z) in profile:
        xo = CX + R_OUTER * cos_t + tang * (-sin_t)
        yo = CY + R_OUTER * sin_t + tang *   cos_t
        ov.append(bm.verts.new((xo, yo, z)))

        xi = CX + R_INNER * cos_t + tang * (-sin_t)
        yi = CY + R_INNER * sin_t + tang *   cos_t
        iv.append(bm.verts.new((xi, yi, z)))

    bm.faces.new(ov[::-1])   # outer cap — normal outward
    bm.faces.new(iv)          # inner cap — normal inward
    for j in range(NP):
        nj = (j + 1) % NP
        bm.faces.new([ov[j], iv[j], iv[nj], ov[nj]])

bm.normal_update()

me = bpy.data.meshes.new("RocketCutters")
bm.to_mesh(me); bm.free(); me.update(); me.validate()
print("Cutter: %d verts, %d faces" % (len(me.vertices), len(me.polygons)))

cutter = bpy.data.objects.new("RocketCutters", me)
bpy.context.collection.objects.link(cutter)

# ── Boolean Difference ──────────────────────────────────────────────────────
cup = bpy.data.objects[CUP_NAME]
bpy.context.view_layer.objects.active = cup
cup.select_set(True)

mod = cup.modifiers.new("RocketCuts", "BOOLEAN")
mod.operation = 'DIFFERENCE'
mod.object    = cutter
mod.solver    = 'EXACT'

print("Applying Boolean via depsgraph (may take a moment)...")
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
cup_eval = cup.evaluated_get(dg)
me_baked = bpy.data.meshes.new_from_object(cup_eval)

me_old = cup.data
cup.modifiers.clear()
cup.data = me_baked
bpy.data.meshes.remove(me_old, do_unlink=True)
print("Boolean applied! New mesh: %d verts" % len(cup.data.vertices))

bpy.data.objects.remove(cutter, do_unlink=True)
bpy.data.meshes.remove(me, do_unlink=True)

print("Done: %d rocket indentations." % N_ROCKETS)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("Saved:", BLEND_PATH)
