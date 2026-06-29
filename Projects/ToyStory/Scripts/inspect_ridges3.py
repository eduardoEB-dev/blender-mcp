import bpy, numpy as np, math

cup = bpy.data.objects['EFCooler_Cup']
mesh = cup.data
mw = cup.matrix_world
verts = [mw @ v.co for v in mesh.vertices]
CX, CY = 43.94, 44.45
zs = np.array([v.z for v in verts])
xs = np.array([v.x for v in verts]) - CX
ys = np.array([v.y for v in verts]) - CY
radii = np.sqrt(xs**2 + ys**2)
angles_rad = np.arctan2(ys, xs)
angles_deg = np.degrees(angles_rad)

# Zone Z 5-30: the deep groove region
zmask = (zs >= 5.0) & (zs < 30.0)
r_zone = radii[zmask]
a_zone = angles_deg[zmask]

print("=== Z 5-30 GROOVE ZONE ===")
print("  Verts: %d  rMin=%.2f  rMax=%.2f" % (zmask.sum(), r_zone.min(), r_zone.max()))

# Tight threshold to capture only the deepest inner-groove verts
for thresh_label, thresh in [("r < 35", 35.0), ("r < 36", 36.0), ("r < 38", 38.0)]:
    inner = r_zone < thresh
    ai = a_zone[inner]
    print("\n  Angular dist of verts with %s  (n=%d):" % (thresh_label, inner.sum()))
    # 72 bins = 5-degree each
    hist, edges = np.histogram(ai, bins=72, range=(-180, 180))
    for i, cnt in enumerate(hist):
        ang = edges[i]
        if cnt > 0:
            bar = '#' * (cnt // 3)
            print("    %7.1f deg: %4d %s" % (ang, cnt, bar))

# Also check at a SINGLE Z level (say Z=15) for angular distribution
print()
print("=== At Z=15 only, inner vertices ===")
z_single = (zs >= 14.5) & (zs < 15.5)
r_s = radii[z_single]
a_s = angles_deg[z_single]
print("  Total at Z=15: %d, rMin=%.2f, rMax=%.2f" % (z_single.sum(), r_s.min(), r_s.max()))
inner_s = r_s < 36.0
ai_s = a_s[inner_s]
print("  Inner verts (r<36): %d" % inner_s.sum())
hist2, edges2 = np.histogram(ai_s, bins=72, range=(-180, 180))
for i, cnt in enumerate(hist2):
    if cnt > 0:
        print("    %7.1f deg: %3d" % (edges2[i], cnt))
