import bpy

# ============================================================
#  Angel Cup — Nose Centering + Eye Symmetry Fix
#  Run via Blender MCP socket or Scripting workspace
# ============================================================

OBJECT_NAME   = "AngelCupSTL"
EYE_MIN_X_DIST = 10.0   # min |X from centre| to count as eye (not nose)
Y_FRONT_PCTG   = 0.20   # top 20% of Y depth = front-face slice

# Set these after reading the Z histogram below (leave None for histogram only).
Z_FACE_MIN = None   # e.g. 55.0
Z_FACE_MAX = None   # e.g. 95.0

DRY_RUN = True   # set False to actually move vertices
# ─────────────────────────────────────────────────────────────

obj = bpy.data.objects.get(OBJECT_NAME)
if obj is None:
    names = [o.name for o in bpy.data.objects]
    raise RuntimeError(f"'{OBJECT_NAME}' not found. Objects: {names}")

if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

mesh = obj.data
mat  = obj.matrix_world
inv  = mat.inverted()

verts_ws = [(v.index, mat @ v.co) for v in mesh.vertices]
xs = [p.x for _, p in verts_ws]
ys = [p.y for _, p in verts_ws]
zs = [p.z for _, p in verts_ws]

x_min, x_max = min(xs), max(xs)
y_min, y_max = min(ys), max(ys)
x_center = (x_min + x_max) / 2

print("=" * 60)
print("  Nose + Eye Symmetry Analyzer  --  " + obj.name)
print("=" * 60)
print("  Vertices : " + str(len(mesh.vertices)))
print("  X centre : " + str(round(x_center, 2)) + "   range " + str(round(x_min,2)) + "-" + str(round(x_max,2)))
print("  Z range  : " + str(round(min(zs),2)) + "-" + str(round(max(zs),2)))

# Front-face slice
y_thresh   = y_max - (y_max - y_min) * Y_FRONT_PCTG
face_verts = [(i, p) for i, p in verts_ws if p.y >= y_thresh]

# Z histogram
bin_mm = 3.0
z_lo   = min(p.z for _, p in face_verts)
z_hi   = max(p.z for _, p in face_verts)
n_bins = int((z_hi - z_lo) / bin_mm) + 1
bins   = [0] * n_bins

for _, p in face_verts:
    b = min(int((p.z - z_lo) / bin_mm), n_bins - 1)
    bins[b] += 1

peak  = max(bins) or 1
bar_w = 35

print("\n  Z HISTOGRAM of front face (3 mm bins):")
print("  Z start    count  bar")
for b, cnt in enumerate(bins):
    z_s    = z_lo + b * bin_mm
    bar    = '#' * int(cnt / peak * bar_w)
    tag    = ""
    if Z_FACE_MIN is not None and Z_FACE_MAX is not None:
        if Z_FACE_MIN <= z_s < Z_FACE_MAX:
            tag = " <- face band"
    print("  " + str(round(z_s,1)).rjust(6) + "-" + str(round(z_s+bin_mm,1)).ljust(5) +
          "  " + str(cnt).rjust(5) + "  " + bar + tag)

if Z_FACE_MIN is None or Z_FACE_MAX is None:
    print("\n  *** Set Z_FACE_MIN and Z_FACE_MAX then re-run for corrections. ***")
else:
    band  = [(i, p) for i, p in face_verts if Z_FACE_MIN <= p.z <= Z_FACE_MAX]
    nose  = [(i, p) for i, p in band if abs(p.x - x_center) < EYE_MIN_X_DIST]
    left  = [(i, p) for i, p in band if p.x < x_center - EYE_MIN_X_DIST]
    right = [(i, p) for i, p in band if p.x > x_center + EYE_MIN_X_DIST]

    def region_info(label, items):
        if not items:
            print("  " + label + ": NO VERTICES -- widen Z_FACE range or adjust EYE_MIN_X_DIST")
            return None, None
        lxs = [p.x for _, p in items]
        lzs = [p.z for _, p in items]
        cx  = (min(lxs) + max(lxs)) / 2
        cz  = (min(lzs) + max(lzs)) / 2
        print("\n  " + label + " (" + str(len(items)) + " verts)")
        print("    X: [" + str(round(min(lxs),2)) + ", " + str(round(max(lxs),2)) + "]  centre=" + str(round(cx,2)))
        print("    Z: [" + str(round(min(lzs),2)) + ", " + str(round(max(lzs),2)) + "]  centre=" + str(round(cz,2)))
        return cx, cz

    print("\n  Face band Z " + str(Z_FACE_MIN) + "-" + str(Z_FACE_MAX) + ": " + str(len(band)) + " verts")
    nose_cx, nose_cz = region_info("NOSE      (centre region)", nose)
    left_cx, left_cz = region_info("LEFT  EYE (viewer left )", left)
    right_cx, right_cz = region_info("RIGHT EYE (viewer right)", right)

    if None in (nose_cx, left_cx, right_cx):
        print("\n  *** Adjust Z_FACE_MIN/MAX or EYE_MIN_X_DIST and re-run. ***")
    else:
        delta_nose_x     = x_center - nose_cx
        expected_left_cx = x_center - (right_cx - x_center)
        delta_left_x     = expected_left_cx - left_cx
        delta_left_z     = right_cz - left_cz

        print("\n" + "=" * 60)
        print("  PLANNED CORRECTIONS")
        print("=" * 60)
        print("  NOSE     move X : " + str(round(delta_nose_x, 4)))
        print("  LEFT EYE move X : " + str(round(delta_left_x, 4)))
        print("  LEFT EYE move Z : " + str(round(delta_left_z, 4)))
        print("  RIGHT EYE       : unchanged (reference)")

        if DRY_RUN:
            print("\n  *** DRY RUN -- nothing moved. Set DRY_RUN=False to apply. ***")
        else:
            for idx, wp in nose:
                v = mesh.vertices[idx]
                w = wp.copy(); w.x += delta_nose_x
                v.co = inv @ w

            for idx, wp in left:
                v = mesh.vertices[idx]
                w = wp.copy()
                w.x += delta_left_x
                w.z += delta_left_z
                v.co = inv @ w

            mesh.update()
            print("\n  DONE!")
            print("  Nose    : " + str(len(nose)) + " verts  X " + str(round(delta_nose_x,4)))
            print("  Left eye: " + str(len(left)) + " verts  X " + str(round(delta_left_x,4)) + "  Z " + str(round(delta_left_z,4)))
            print("  Use Ctrl+Z to undo.")
