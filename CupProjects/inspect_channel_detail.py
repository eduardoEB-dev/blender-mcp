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
angles_deg = np.degrees(np.arctan2(ys, xs))

# Look at multiple Z levels to find channel geometry
for z_target in [42.0, 45.0, 57.0, 70.0, 73.0]:
    zmask = (zs >= z_target - 0.6) & (zs < z_target + 0.6)
    if zmask.sum() < 4:
        print("Z=%.1f: no verts" % z_target)
        continue
    r_z = radii[zmask]; a_z = angles_deg[zmask]
    r_min = r_z.min(); r_max = r_z.max()
    print("Z=%.1f: %d verts, rMin=%.3f rMax=%.3f range=%.3f" % (
        z_target, zmask.sum(), r_min, r_max, r_max - r_min))

    # Show fine-grained angular distribution (1-degree bins)
    if zmask.sum() > 10:
        hist, edges = np.histogram(a_z, bins=360, range=(-180, 180))
        # Show non-zero bins
        nonzero = [(edges[i], hist[i]) for i in range(360) if hist[i] > 0]
        if len(nonzero) <= 60:
            for ang, cnt in nonzero:
                print("  %7.1f deg: %d" % (ang, cnt))
        else:
            print("  Too many bins (%d non-zero) - sampling inner verts only" % len(nonzero))
            inner = r_z < (r_min + (r_max - r_min) * 0.3)
            a_inner = a_z[inner]
            if len(a_inner) > 0:
                hi, ei = np.histogram(a_inner, bins=360, range=(-180, 180))
                nonzero_i = [(ei[i], hi[i]) for i in range(360) if hi[i] > 0]
                print("  Inner verts (n=%d) angular distribution:" % len(a_inner))
                for ang, cnt in nonzero_i:
                    print("    %7.1f deg: %d" % (ang, cnt))
    print()

# More specific: at Z=50 (channel middle), show all vertex radii by angle
print("=== ALL VERTS AT Z=50 (no verts?), trying Z=57 ===")
for z_try in [47, 50, 55, 57, 60, 65]:
    zmask = (zs >= z_try - 0.2) & (zs < z_try + 0.2)
    print("  Z=%d: %d verts" % (z_try, zmask.sum()))
