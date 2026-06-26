import bpy, bmesh, math

CX, CY     = 43.94, 44.45
Z_GRIP_BOT = 43.0
Z_GRIP_TOP = 71.0
R_OUTER    = 43.5   # only touch outer-surface verts (inner wall is ~41mm)
R_MAX      = 47.0

cup = bpy.data.objects['EFCooler_Cup']
bm = bmesh.new()
bm.from_mesh(cup.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

def on_outer_grip(v):
    z = v.co.z
    if z < Z_GRIP_BOT or z > Z_GRIP_TOP:
        return False
    dx = v.co.x - CX;  dy = v.co.y - CY
    r = math.sqrt(dx*dx + dy*dy)
    return R_OUTER <= r <= R_MAX

def project_to_cylinder(v, target_r):
    dx = v.co.x - CX;  dy = v.co.y - CY
    r = math.sqrt(dx*dx + dy*dy)
    if r < 1e-6:
        return
    scale = target_r / r
    v.co.x = CX + dx * scale
    v.co.y = CY + dy * scale

# Compute target radius per Z by taking the 95th-percentile radius
# of all outer grip-band vertices (they're already on the cylinder)
from collections import defaultdict
z_bins = defaultdict(list)
for v in bm.verts:
    if on_outer_grip(v):
        zk = round(v.co.z * 2) / 2
        dx = v.co.x - CX;  dy = v.co.y - CY
        z_bins[zk].append(math.sqrt(dx*dx + dy*dy))

z_target = {}
for zk, rlist in z_bins.items():
    rlist.sort()
    z_target[zk] = rlist[int(len(rlist)*0.95)]

def interp_r(z):
    keys = sorted(z_target.keys())
    if not keys:
        return 44.0
    if z <= keys[0]:  return z_target[keys[0]]
    if z >= keys[-1]: return z_target[keys[-1]]
    for i in range(len(keys)-1):
        if keys[i] <= z <= keys[i+1]:
            t = (z - keys[i]) / (keys[i+1] - keys[i])
            return z_target[keys[i]] * (1-t) + z_target[keys[i+1]] * t
    return 44.0

# Find edges where BOTH endpoints are on the outer grip surface
# and the edge spans more than MAX_ARC degrees — these are the
# "too-wide" edges in the flat patches that need subdividing.
MAX_ARC_DEG = 1.5   # edges spanning more than this get subdivided

edges_to_sub = []
for e in bm.edges:
    v0, v1 = e.verts
    if not (on_outer_grip(v0) and on_outer_grip(v1)):
        continue
    # angular span between the two verts
    a0 = math.atan2(v0.co.y - CY, v0.co.x - CX)
    a1 = math.atan2(v1.co.y - CY, v1.co.x - CX)
    diff = abs(math.degrees(a1 - a0))
    if diff > 180: diff = 360 - diff
    if diff > MAX_ARC_DEG:
        edges_to_sub.append(e)

print("Edges to subdivide: %d" % len(edges_to_sub))

if edges_to_sub:
    result = bmesh.ops.subdivide_edges(bm, edges=edges_to_sub, cuts=2, use_grid_fill=True)
    # Project all new verts to the cylinder
    new_verts = [v for v in result.get('geom_split', []) if isinstance(v, bmesh.types.BMVert)]
    projected = 0
    for v in new_verts:
        if on_outer_grip(v):
            project_to_cylinder(v, interp_r(v.co.z))
            projected += 1
    print("Projected %d new verts to cylinder" % projected)

bm.normal_update()
bm.to_mesh(cup.data)
bm.free()
cup.data.update()
bpy.ops.wm.save_as_mainfile(filepath=r"d:\Blender\RocketCup_smooth.blend")
print("Done. Verts: %d" % len(cup.data.vertices))
