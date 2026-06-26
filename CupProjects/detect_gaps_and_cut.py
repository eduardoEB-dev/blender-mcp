import bpy, bmesh, math
import numpy as np

CUP_NAME  = 'EFCooler_Cup'
CX, CY    = 43.94, 44.45
R_OUTER   = 44.7
R_INNER   = 42.2

BODY_HW   = 1.5
BODY_NAR  = 1.0
WING_HW   = 2.5
WING_TIP  = 2.1
Z_MAX     = 71.0
Z_NS      = 65.0
Z_BODY    = 59.0
Z_WR      = 53.0
Z_WMAX    = 49.0
Z_NOTCH   = 47.0
Z_MIN     = 43.0

rocket_profile = [
    ( 0.0,      Z_MAX),
    (-BODY_HW,  Z_NS),
    (-BODY_HW,  Z_BODY),
    (-BODY_NAR, Z_WR),
    (-WING_HW,  Z_WMAX),
    (-WING_TIP, Z_MIN),
    ( 0.0,      Z_NOTCH),
    ( WING_TIP, Z_MIN),
    ( WING_HW,  Z_WMAX),
    ( BODY_NAR, Z_WR),
    ( BODY_HW,  Z_BODY),
    ( BODY_HW,  Z_NS),
]

# ── Step 1: detect gap angles ────────────────────────────────────────────────
cup = bpy.data.objects[CUP_NAME]

n = len(cup.data.vertices)
coords = np.zeros(n * 3, dtype=np.float32)
cup.data.vertices.foreach_get('co', coords)
coords = coords.reshape(n, 3)  # local = world (identity matrix_world)

z_all = coords[:, 2]
print("Cup Z: %.3f – %.3f" % (float(z_all.min()), float(z_all.max())))

# The grip band has NO interior vertices — it's a gap in the Z distribution.
# Vertical edges span from the bottom boundary ring to the top boundary ring.
# Detect gap: find where the Z distribution jumps.
z_sorted = np.sort(z_all)
# Find the largest Z gap — that's the grip band empty region
gaps = np.diff(z_sorted)
big_gap_idx = int(np.argmax(gaps))
GAP_BOT = float(z_sorted[big_gap_idx])      # Z just before the gap
GAP_TOP = float(z_sorted[big_gap_idx + 1])  # Z just after the gap
print("Grip band gap detected: Z %.3f to %.3f" % (GAP_BOT, GAP_TOP))

# Find edges that SPAN the grip band gap (one vert below gap, one above).
# These are the actual vertical "lines" visible in the wireframe.
span_angles = []
for e in cup.data.edges:
    i0, i1 = e.vertices[0], e.vertices[1]
    z0, z1 = float(z_all[i0]), float(z_all[i1])
    crosses = ((z0 <= GAP_BOT + 0.1 and z1 >= GAP_TOP - 0.1) or
               (z1 <= GAP_BOT + 0.1 and z0 >= GAP_TOP - 0.1))
    if not crosses:
        continue
    # Midpoint angle of this spanning edge
    mx = (coords[i0, 0] + coords[i1, 0]) / 2.0
    my = (coords[i0, 1] + coords[i1, 1]) / 2.0
    span_angles.append(math.degrees(math.atan2(my - CY, mx - CX)) % 360.0)

print("Spanning grip-band edges: %d" % len(span_angles))
angles_deg = np.array(span_angles) if span_angles else np.array([])

# Histogram with 1° bins, then smooth with 11° window to reveal channel-scale pattern
N_BINS = 360
hist, bin_edges = np.histogram(angles_deg, bins=N_BINS, range=(0, 360))
print("Angle histogram (nonzero bins): %d / %d" % (np.sum(hist > 0), N_BINS))

W = 11  # smoothing half-window in degrees
kernel = np.ones(W) / W
# Wrap-around smoothing via tiling
hist_ext = np.concatenate([hist[-W:], hist, hist[:W]])
smooth_ext = np.convolve(hist_ext, kernel, mode='same')
smooth = smooth_ext[W:-W]

# Find local minima — positions lower than both neighbours within ±MIN_SEP degrees
MIN_SEP = 8  # minimum degrees between two separate rockets
candidates = []
for i in range(N_BINS):
    is_min = all(smooth[i] <= smooth[(i + d) % N_BINS] for d in range(-MIN_SEP, MIN_SEP + 1) if d != 0)
    if is_min:
        candidates.append((float(smooth[i]), float(i)))  # (depth, angle_bin)

# Sort by depth (lowest first) — deepest valleys = clearest empty spaces
candidates.sort()

# Greedily pick minima that are at least MIN_SEP degrees apart (circular)
selected = []
for depth, angle_bin in candidates:
    too_close = False
    for prev_bin in selected:
        diff = abs(angle_bin - prev_bin)
        if diff > 180: diff = 360 - diff
        if diff < MIN_SEP:
            too_close = True
            break
    if not too_close:
        selected.append(angle_bin)

# Convert to degree values (center of each bin)
gap_centers = sorted([b + 0.5 for b in selected])
print("Detected %d gap centers: %s" % (
    len(gap_centers),
    [round(g, 1) for g in gap_centers]
))

rocket_angles = [math.radians(g) for g in gap_centers]
N_ROCKETS = len(rocket_angles)

if N_ROCKETS == 0:
    print("ERROR: no gaps detected — aborting")
    import sys; sys.exit(1)

# ── Step 2: build cutter prism for each detected gap angle ───────────────────
def add_prism(bm, profile, theta):
    ct, st = math.cos(theta), math.sin(theta)
    NP = len(profile)
    ov, iv = [], []
    for (tang, z) in profile:
        ov.append(bm.verts.new((CX + R_OUTER*ct + tang*(-st), CY + R_OUTER*st + tang*ct, z)))
        iv.append(bm.verts.new((CX + R_INNER*ct + tang*(-st), CY + R_INNER*st + tang*ct, z)))
    bm.faces.new(ov[::-1])
    bm.faces.new(iv)
    for j in range(NP):
        nj = (j + 1) % NP
        bm.faces.new([ov[j], iv[j], iv[nj], ov[nj]])

bm = bmesh.new()
for theta in rocket_angles:
    add_prism(bm, rocket_profile, theta)

bm.normal_update()
me = bpy.data.meshes.new("RocketCuts")
bm.to_mesh(me); bm.free(); me.update(); me.validate()
print("Cutter: %d verts / %d faces" % (len(me.vertices), len(me.polygons)))

cutter = bpy.data.objects.new("RocketCuts", me)
bpy.context.collection.objects.link(cutter)

print("Cup before: %d verts" % len(cup.data.vertices))

mod = cup.modifiers.new("RocketCuts", "BOOLEAN")
mod.operation = 'DIFFERENCE'
mod.object    = cutter
mod.solver    = 'EXACT'

bpy.context.view_layer.objects.active = cup
cup.select_set(True)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
cup_eval = cup.evaluated_get(dg)
me_baked = bpy.data.meshes.new_from_object(cup_eval)
me_old = cup.data
cup.modifiers.clear()
cup.data = me_baked
bpy.data.meshes.remove(me_old, do_unlink=True)
bpy.data.objects.remove(cutter, do_unlink=True)
print("Cup after Boolean: %d verts" % len(cup.data.vertices))

# ── Step 3: post-process — move V-tip vertices to R_INNER and merge ──────────
bm2 = bmesh.new()
bm2.from_mesh(cup.data)
bm2.verts.ensure_lookup_table()

moved = 0
for theta in rocket_angles:
    ct, st = math.cos(theta), math.sin(theta)
    best, best_r = None, 0.0
    for v in bm2.verts:
        if abs(v.co.z - Z_NOTCH) > 0.05:
            continue
        dx = v.co.x - CX
        dy = v.co.y - CY
        r  = math.sqrt(dx*dx + dy*dy)
        if r < R_INNER + 0.3 or r > R_OUTER:
            continue
        tang = -dx * st + dy * ct
        if abs(tang) > 0.15:
            continue
        ang = math.atan2(dy, dx)
        diff = abs(ang - theta)
        if diff > math.pi: diff = 2*math.pi - diff
        if diff > math.radians(6):
            continue
        if r > best_r:
            best_r = r; best = v
    if best:
        best.co.x = CX + R_INNER * ct
        best.co.y = CY + R_INNER * st
        best.co.z = Z_NOTCH
        moved += 1
    else:
        print("WARNING: rocket at %.1f° — V-tip not found" % math.degrees(theta))

print("V-tip vertices moved: %d / %d" % (moved, N_ROCKETS))
bmesh.ops.remove_doubles(bm2, verts=bm2.verts, dist=0.05)
bm2.normal_update()
bm2.to_mesh(cup.data)
bm2.free()
cup.data.update()

bpy.ops.wm.save_as_mainfile(filepath=r"d:\Blender\RocketCup.blend")
print("Saved to RocketCup.blend")
