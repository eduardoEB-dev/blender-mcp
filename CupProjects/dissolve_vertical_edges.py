import bpy, bmesh, math

CX, CY = 43.94, 44.45

cup = bpy.data.objects['EFCooler_Cup']
mw  = cup.matrix_world

# Auto-detect full Z range
zs_all = [(mw @ v.co).z for v in cup.data.vertices]
Z_BOT = min(zs_all)
Z_TOP = max(zs_all)
print("Cup Z range: %.3f to %.3f" % (Z_BOT, Z_TOP))

# Grip band is roughly Z=43-71mm on a 116mm cup
# Scale proportionally
Z_GRIP_BOT = Z_BOT + (Z_TOP - Z_BOT) * 0.355
Z_GRIP_TOP = Z_BOT + (Z_TOP - Z_BOT) * 0.615
print("Grip band: Z %.3f to %.3f" % (Z_GRIP_BOT, Z_GRIP_TOP))

bm = bmesh.new()
bm.from_mesh(cup.data)
bm.edges.ensure_lookup_table()

edges_to_dissolve = []
checked = 0
for e in bm.edges:
    v0, v1 = e.verts
    w0 = mw @ v0.co
    w1 = mw @ v1.co
    z0, z1 = w0.z, w1.z

    # At least one vertex must be inside the grip band (inclusive of boundary)
    in0 = Z_GRIP_BOT - 0.1 <= z0 <= Z_GRIP_TOP + 0.1
    in1 = Z_GRIP_BOT - 0.1 <= z1 <= Z_GRIP_TOP + 0.1
    if not (in0 and in1):
        continue

    # Outer surface only
    r0 = math.sqrt((w0.x - CX)**2 + (w0.y - CY)**2)
    r1 = math.sqrt((w1.x - CX)**2 + (w1.y - CY)**2)
    R_LO, R_HI = 40.0, 47.0
    if not (R_LO < r0 < R_HI and R_LO < r1 < R_HI):
        continue

    checked += 1
    dz    = abs(z1 - z0)
    dtang = math.sqrt((w1.x - w0.x)**2 + (w1.y - w0.y)**2)

    # Skip horizontal edges (both verts at same Z — these are the ring loops to keep)
    if dz < 0.01:
        continue
    # Skip diagonal edges
    if dtang > dz * 0.3:
        continue

    edges_to_dissolve.append(e)

print("Grip band outer edges checked: %d" % checked)
print("Vertical edges to dissolve: %d" % len(edges_to_dissolve))

if edges_to_dissolve:
    bmesh.ops.dissolve_edges(bm, edges=edges_to_dissolve,
                             use_verts=True, use_face_split=False)

bm.normal_update()
bm.to_mesh(cup.data)
bm.free()
cup.data.update()
print("After: %d verts, %d edges" % (len(cup.data.vertices), len(cup.data.edges)))
bpy.ops.wm.save_as_mainfile(filepath=r"d:\Blender\RocketCup_smooth.blend")
print("Saved")
