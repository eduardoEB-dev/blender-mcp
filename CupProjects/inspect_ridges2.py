import bpy, numpy as np, math

cup = bpy.data.objects['EFCooler_Cup']
mesh = cup.data
mw = cup.matrix_world
verts = [mw @ v.co for v in mesh.vertices]
zs = np.array([v.z for v in verts])
cx = 43.94; cy = 44.45
xs = np.array([v.x for v in verts]) - cx
ys = np.array([v.y for v in verts]) - cy
radii = np.sqrt(xs**2 + ys**2)
angles = np.degrees(np.arctan2(ys, xs))  # -180 to 180

# Focus on high-density zones: Z 40-47 and Z 69-75
for label, z_lo, z_hi in [("LOWER RIDGE ZONE Z40-47", 40, 47), ("UPPER RIDGE ZONE Z69-76", 69, 76)]:
    print("=== %s ===" % label)
    mask = (zs >= z_lo) & (zs < z_hi)
    r_zone = radii[mask]; a_zone = angles[mask]
    r_min_thresh = r_zone.min() + 0.5  # vertices near the min radius = inside groove
    inner_mask = r_zone < r_min_thresh
    a_inner = a_zone[inner_mask]
    print("  Total verts in zone: %d" % mask.sum())
    print("  Min radius: %.2f  Max radius: %.2f" % (r_zone.min(), r_zone.max()))
    print("  Inner groove verts (r < %.2f): %d" % (r_min_thresh, inner_mask.sum()))
    # Histogram of angles for inner verts (36 bins = 10-degree each)
    if inner_mask.sum() > 0:
        hist, edges = np.histogram(a_inner, bins=36, range=(-180, 180))
        print("  Angular histogram of inner verts (each bin = 10 deg):")
        for i, cnt in enumerate(hist):
            ang = edges[i]
            if cnt > 0:
                bar = '#' * (cnt // 5)
                print("    %6.1f deg: %4d %s" % (ang, cnt, bar))
    print()

# Also check if ridges are at the ENTIRE cup or just in the middle
print("=== FULL CUP RADIUS RANGE by Z ===")
for z0 in range(0, 120, 5):
    z1 = z0 + 5
    mask = (zs >= z0) & (zs < z1)
    if mask.sum() < 10:
        continue
    r = radii[mask]
    rng = r.max() - r.min()
    bar = '#' * int(rng)
    print("  Z %3d-%3d: rMin=%5.2f  rMax=%5.2f  range=%4.2f  %s" % (z0, z1, r.min(), r.max(), rng, bar))

# What's in the Z 45-70 empty zone?
print()
print("=== OBJECT LIST (to check for separate ridge objects) ===")
for obj in bpy.data.objects:
    print("  %r  type=%s" % (obj.name, obj.type))
