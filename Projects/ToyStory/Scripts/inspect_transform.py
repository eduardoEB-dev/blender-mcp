import bpy, numpy as np
from mathutils import Vector

cup = bpy.data.objects['EFCooler_Cup']
mw  = cup.matrix_world

print(f"Location : {list(cup.location)}")
print(f"Rotation (Euler, deg): {[round(r*57.2958,2) for r in cup.rotation_euler]}")
print(f"Scale    : {list(cup.scale)}")

# World-space bounding box
bb_world = [mw @ Vector(c) for c in cup.bound_box]
xs = [v.x for v in bb_world]; ys = [v.y for v in bb_world]; zs = [v.z for v in bb_world]
print(f"\nWorld bounding box:")
print(f"  X: {min(xs):.2f} to {max(xs):.2f}  (width  {max(xs)-min(xs):.2f})")
print(f"  Y: {min(ys):.2f} to {max(ys):.2f}  (depth  {max(ys)-min(ys):.2f})")
print(f"  Z: {min(zs):.2f} to {max(zs):.2f}  (height {max(zs)-min(zs):.2f})")

# Find which direction the majority of "front-smooth-top" polys face
# Front view in Blender = looking along +Y, so front face normals point in -Y direction
poly_data = []
for p in cup.data.polygons:
    wn = (mw.to_3x3() @ p.normal).normalized()
    wc = mw @ p.center
    poly_data.append((wc.x, wc.y, wc.z, wn.x, wn.y, wn.z))
arr = np.array(poly_data)
cx,cy,cz = arr[:,0],arr[:,1],arr[:,2]
nx,ny,nz = arr[:,3],arr[:,4],arr[:,5]

# Polys facing -Y (front face in front view) in the upper smooth region
top_front = arr[(cz > 76) & (ny < -0.3)]
print(f"\nPolys facing -Y (front) in Z>76: {len(top_front)}")
if len(top_front):
    tf = top_front
    print(f"  X: {tf[:,0].min():.1f} to {tf[:,0].max():.1f}  center={tf[:,0].mean():.1f}")
    print(f"  Y: {tf[:,1].min():.1f} to {tf[:,1].max():.1f}  center={tf[:,1].mean():.1f}")
    print(f"  Z: {tf[:,2].min():.1f} to {tf[:,2].max():.1f}  center={tf[:,2].mean():.1f}")

# Also check all 4 cardinal directions to see which has most polys in top region
for label,axis,sign in [('NEG_Y (-front)',4,-1),('POS_Y (+back)',4,1),
                         ('NEG_X (-left)',3,-1),('POS_X (+right)',3,1)]:
    top = arr[(cz > 76)]
    cnt = (top[:,axis]*sign > 0.5).sum()
    print(f"  {label}: {cnt} polys in Z>76")
