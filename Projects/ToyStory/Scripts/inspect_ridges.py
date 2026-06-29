import bpy, numpy as np

cup = bpy.data.objects['EFCooler_Cup']
mesh = cup.data
mw = cup.matrix_world
verts = [mw @ v.co for v in mesh.vertices]
zs = [v.z for v in verts]
cx = 43.94; cy = 44.45
radii = [((v.x - cx)**2 + (v.y - cy)**2)**0.5 for v in verts]
z_arr = np.array(zs); r_arr = np.array(radii)

print("=== RADIUS VARIATION per Z-slice (Z 0-50) ===")
for i in range(50):
    z0 = float(i); z1 = z0 + 1.0
    mask = (z_arr >= z0) & (z_arr < z1)
    cnt = int(mask.sum())
    if cnt < 4:
        continue
    rs = r_arr[mask]
    rng = float(rs.max() - rs.min())
    print("  Z %5.1f-%4.1f: n=%5d  rMin=%5.2f  rMax=%5.2f  range=%5.2f" % (z0, z1, cnt, rs.min(), rs.max(), rng))

print()
print("=== RADIUS VARIATION per Z-slice (Z 60-85) ===")
for i in range(60, 85):
    z0 = float(i); z1 = z0 + 1.0
    mask = (z_arr >= z0) & (z_arr < z1)
    cnt = int(mask.sum())
    if cnt < 4:
        continue
    rs = r_arr[mask]
    rng = float(rs.max() - rs.min())
    print("  Z %5.1f-%4.1f: n=%5d  rMin=%5.2f  rMax=%5.2f  range=%5.2f" % (z0, z1, cnt, rs.min(), rs.max(), rng))
