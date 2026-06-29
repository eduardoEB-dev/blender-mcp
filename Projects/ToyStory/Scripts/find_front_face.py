import bpy, numpy as np
from mathutils import Vector

cup = bpy.data.objects['EFCooler_Cup']
mw  = cup.matrix_world

# Collect all polygon centers + normals in world space
# Focus on the smooth top region Z > 76mm where artwork goes
poly_data = []
for p in cup.data.polygons:
    wn = (mw.to_3x3() @ p.normal).normalized()
    wc = mw @ p.center
    poly_data.append((wc.x, wc.y, wc.z, wn.x, wn.y, wn.z))

arr = np.array(poly_data)
cx,cy,cz,nx,ny,nz = arr[:,0],arr[:,1],arr[:,2],arr[:,3],arr[:,4],arr[:,5]

print(f"Cup centroid XY: ({cx.mean():.2f}, {cy.mean():.2f})")
print(f"Total polys: {len(arr)}")

# Find polys in upper smooth region (Z > 76)
top = arr[cz > 76]
print(f"\nPolys in smooth top region (Z>76): {len(top)}")

# Bucket normals by dominant direction (X vs Y)
dirs = {'POS_X':0,'NEG_X':0,'POS_Y':0,'NEG_Y':0,'POS_Z':0,'NEG_Z':0}
for row in top:
    nx_,ny_,nz_ = row[3],row[4],row[5]
    m = max(abs(nx_),abs(ny_),abs(nz_))
    if   abs(nx_)==m: dirs['POS_X' if nx_>0 else 'NEG_X'] += 1
    elif abs(ny_)==m: dirs['POS_Y' if ny_>0 else 'NEG_Y'] += 1
    else:             dirs['POS_Z' if nz_>0 else 'NEG_Z'] += 1

print("\nNormal direction counts (top region):")
for k,v in sorted(dirs.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

# For each direction find the centroid of polys facing that way (threshold 0.5)
print("\nCentroid + bounds per dominant direction in top region:")
for label,axis,sign in [('POS_X',3,1),('NEG_X',3,-1),('POS_Y',4,1),('NEG_Y',4,-1)]:
    mask = top[:,axis]*sign > 0.5
    sub  = top[mask]
    if len(sub):
        print(f"  {label} ({len(sub)} polys): "
              f"X {sub[:,0].min():.1f}-{sub[:,0].max():.1f}  "
              f"Y {sub[:,1].min():.1f}-{sub[:,1].max():.1f}  "
              f"Z {sub[:,2].min():.1f}-{sub[:,2].max():.1f}  "
              f"centroid ({sub[:,0].mean():.1f},{sub[:,1].mean():.1f},{sub[:,2].mean():.1f})")

# Also find the bottom hole center (lowest Z verts in a ring)
verts = np.array([list(mw @ v.co) for v in cup.data.vertices])
bottom = verts[verts[:,2] < 5]
print(f"\nBottom ring centroid: ({bottom[:,0].mean():.2f},{bottom[:,1].mean():.2f},{bottom[:,2].mean():.2f})")
print(f"Bottom ring XY range: X {bottom[:,0].min():.1f}-{bottom[:,0].max():.1f}  Y {bottom[:,1].min():.1f}-{bottom[:,1].max():.1f}")
