import bpy, bmesh, math

CUP_NAME  = 'EFCooler_Cup'
CX, CY    = 43.94, 44.45
N_ROCKETS = 30
R_OUTER   = 44.7
R_INNER   = 42.2

BODY_HW   = 1.5
BODY_NAR  = 1.0
WING_HW   = 2.5
WING_TIP  = 2.1
Z_MAX     = 71.0
Z_NS      = 65.0
Z_BODY    = 59.0
Z_WR      = 53.0
Z_WMAX    = 49.0
Z_NOTCH   = 47.0
Z_MIN     = 43.0

rocket_profile = [
    ( 0.0,      Z_MAX),
    (-BODY_HW,  Z_NS),
    (-BODY_HW,  Z_BODY),
    (-BODY_NAR, Z_WR),
    (-WING_HW,  Z_WMAX),
    (-WING_TIP, Z_MIN),
    ( 0.0,      Z_NOTCH),
    ( WING_TIP, Z_MIN),
    ( WING_HW,  Z_WMAX),
    ( BODY_NAR, Z_WR),
    ( BODY_HW,  Z_BODY),
    ( BODY_HW,  Z_NS),
]

def add_prism(bm, profile, theta):
    ct, st = math.cos(theta), math.sin(theta)
    NP = len(profile)
    ov, iv = [], []
    for (tang, z) in profile:
        ov.append(bm.verts.new((CX + R_OUTER*ct + tang*(-st), CY + R_OUTER*st + tang*ct, z)))
        iv.append(bm.verts.new((CX + R_INNER*ct + tang*(-st), CY + R_INNER*st + tang*ct, z)))
    bm.faces.new(ov[::-1])
    bm.faces.new(iv)
    for j in range(NP):
        nj = (j + 1) % NP
        bm.faces.new([ov[j], iv[j], iv[nj], ov[nj]])

bm = bmesh.new()
for i in range(N_ROCKETS):
    add_prism(bm, rocket_profile, math.radians(i * 360.0 / N_ROCKETS))

bm.normal_update()
me = bpy.data.meshes.new("RocketCuts")
bm.to_mesh(me); bm.free(); me.update(); me.validate()
print("Cutter: %d verts / %d faces" % (len(me.vertices), len(me.polygons)))

cutter = bpy.data.objects.new("RocketCuts", me)
bpy.context.collection.objects.link(cutter)

cup = bpy.data.objects[CUP_NAME]
print("Cup before: %d verts" % len(cup.data.vertices))

mod = cup.modifiers.new("RocketCuts", "BOOLEAN")
mod.operation = 'DIFFERENCE'
mod.object    = cutter
mod.solver    = 'EXACT'

bpy.context.view_layer.objects.active = cup
cup.select_set(True)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
cup_eval = cup.evaluated_get(dg)
me_baked = bpy.data.meshes.new_from_object(cup_eval)
me_old = cup.data
cup.modifiers.clear()
cup.data = me_baked
bpy.data.meshes.remove(me_old, do_unlink=True)
bpy.data.objects.remove(cutter, do_unlink=True)
print("Cup after Boolean: %d verts" % len(cup.data.vertices))

# Post-process: move the 30 V-tip vertices from the outer cup surface to R_INNER,
# then merge with the existing inner-wall vertex at the same position.
# The V-tip for rocket i is the vertex at (tang≈0, Z≈Z_NOTCH, r > R_INNER)
# closest to the radial center of each rocket.
bm2 = bmesh.new()
bm2.from_mesh(cup.data)
bm2.verts.ensure_lookup_table()

moved = 0
for i in range(N_ROCKETS):
    theta = math.radians(i * 360.0 / N_ROCKETS)
    ct, st = math.cos(theta), math.sin(theta)

    best, best_r = None, 0.0
    for v in bm2.verts:
        # EXACT solver places V-tip at precisely Z=Z_NOTCH — use tight tolerance
        if abs(v.co.z - Z_NOTCH) > 0.05:
            continue
        dx = v.co.x - CX
        dy = v.co.y - CY
        r = math.sqrt(dx*dx + dy*dy)
        if r < R_INNER + 0.3 or r > R_OUTER:
            continue
        tang = -dx * st + dy * ct
        if abs(tang) > 0.15:   # very tight — V-tip is exactly at tang=0
            continue
        ang = math.atan2(dy, dx)
        diff = abs(ang - theta)
        if diff > math.pi: diff = 2*math.pi - diff
        if diff > math.radians(4):
            continue
        if r > best_r:
            best_r = r
            best = v

    if best:
        best.co.x = CX + R_INNER * ct
        best.co.y = CY + R_INNER * st
        best.co.z = Z_NOTCH
        moved += 1
    else:
        print("WARNING: rocket %d — V-tip vertex not found" % i)

print("V-tip vertices moved: %d / %d" % (moved, N_ROCKETS))
bmesh.ops.remove_doubles(bm2, verts=bm2.verts, dist=0.05)
bm2.normal_update()
bm2.to_mesh(cup.data)
bm2.free()
cup.data.update()
print("Cup after post-process: %d verts" % len(cup.data.vertices))

bpy.ops.wm.save_as_mainfile(filepath=r"d:\Blender\RocketCup.blend")
print("Saved")
