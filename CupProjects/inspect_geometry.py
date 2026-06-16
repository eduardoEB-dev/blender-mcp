import bpy
import numpy as np
from mathutils import Vector

cup = bpy.data.objects['EFCooler_Cup']
mesh = cup.data
mw = cup.matrix_world

# Get all world-space vertices
verts = np.array([list(mw @ v.co) for v in mesh.vertices])

# Cup center in XY
cx = (verts[:,0].max() + verts[:,0].min()) / 2
cy = (verts[:,1].max() + verts[:,1].min()) / 2
print(f"Cup center XY: ({cx:.2f}, {cy:.2f})")
print(f"Cup Z range: {verts[:,2].min():.2f} to {verts[:,2].max():.2f}")

# Find "front face" vertices: those with high Y and near center X
# Front = max Y direction
front_thresh = verts[:,1].max() - 5  # within 5mm of front
front_verts = verts[verts[:,1] > front_thresh]
print(f"\nFront-facing verts (Y > {front_thresh:.1f}): {len(front_verts)}")
if len(front_verts):
    print(f"  Z range of front verts: {front_verts[:,2].min():.2f} to {front_verts[:,2].max():.2f}")

# Analyze vertex density per Z slice to find ridged vs smooth regions
z_min = verts[:,2].min()
z_max = verts[:,2].max()
n_slices = 40
slice_h = (z_max - z_min) / n_slices
print(f"\nVertex density by Z slice (to find ridged regions):")
for i in range(n_slices):
    z_lo = z_min + i * slice_h
    z_hi = z_lo + slice_h
    count = np.sum((verts[:,2] >= z_lo) & (verts[:,2] < z_hi))
    bar = '#' * (count // 5)
    print(f"  Z {z_lo:5.1f}-{z_hi:5.1f}: {count:4d} {bar}")

# Find face normals pointing toward +Y (front face)
print("\n=== Front-facing polygon Z ranges ===")
front_polys_z = []
for poly in mesh.polygons:
    world_normal = mw.to_3x3() @ poly.normal
    if world_normal.y > 0.3:  # facing front
        center = mw @ poly.center
        front_polys_z.append(center.z)

if front_polys_z:
    front_polys_z = sorted(front_polys_z)
    print(f"Front-facing polys Z: {min(front_polys_z):.2f} to {max(front_polys_z):.2f}")
    # Bin them
    bins = np.histogram(front_polys_z, bins=20)
    for i, (count, edge) in enumerate(zip(bins[0], bins[1])):
        bar = '#' * (count // 2)
        print(f"  Z {edge:5.1f}: {count:3d} {bar}")
