import bpy, bmesh, math

CUP_NAME  = 'EFCooler_Cup'
CX, CY    = 43.94, 44.45
N_ROCKETS = 30
R_OUTER   = 44.7
R_INNER   = 42.2

# SVG-derived proportions from 04_White.svg (Buzz Badge white rocket silhouette)
# Body widens from nose, stays wide, then narrows at wing root
# Wings sweep outward to max width, then taper back to tips at bottom
BODY_HW   = 1.5   # body half-width (mm)
BODY_NAR  = 1.0   # body half-width at wing root (narrows toward base)
WING_HW   = 2.5   # wing outer half-width at maximum (slightly wider for visibility)
WING_TIP  = 2.1   # wing half-width at bottom tip

Z_MAX  = 77.0  # nose tip  = top of original channel caps (measured: Z=77)
Z_NS   = 71.0  # nose shoulder
Z_BODY = 60.0  # body at full width
Z_WR   = 51.0  # wing root (body narrows here, wings start)
Z_WMAX = 45.0  # wing maximum width
Z_NOTCH = 41.0 # center notch height — rises 4mm above wing tips for visible "M" shape
Z_MIN  = 37.0  # wing tips = bottom of original channel caps (measured: Z=37)

# Profile shape (tang=tangential mm, Z=vertical mm):
#
#        (0, 77)                 ← nose tip
#   (-1.5,71) (1.5,71)          ← nose shoulder
#   (-1.5,60) (1.5,60)          ← body full width
#   (-1.0,51) (1.0,51)          ← wing root (body narrows)
#   (-2.5,45) (2.5,45)          ← wing max (swept outward)
#   (-2.1,37) (2.1,37)          ← wing tips (2 downward points of the "M")
#        (0, 41)                 ← center notch (valley of "M", 4mm above tips)
#
profile = [
    ( 0.0,      Z_MAX),    # 0  nose tip
    (-BODY_HW,  Z_NS),     # 1  L nose shoulder
    (-BODY_HW,  Z_BODY),   # 2  L body full width
    (-BODY_NAR, Z_WR),     # 3  L body narrows at wing root
    (-WING_HW,  Z_WMAX),   # 4  L wing outer maximum (swept out + down)
    (-WING_TIP, Z_MIN),    # 5  L wing bottom tip (outer "M" peak, pointing down)
    ( 0.0,      Z_NOTCH),  # 6  center notch (valley of "M", rises 4mm above tips)
    ( WING_TIP, Z_MIN),    # 7  R wing bottom tip
    ( WING_HW,  Z_WMAX),   # 8  R wing outer maximum
    ( BODY_NAR, Z_WR),     # 9  R body at wing root
    ( BODY_HW,  Z_BODY),   # 10 R body full width
    ( BODY_HW,  Z_NS),     # 11 R nose shoulder
]
NP = len(profile)

print("Building %d rocket cutters..." % N_ROCKETS)
bm = bmesh.new()
for i in range(N_ROCKETS):
    theta = math.radians(i * 360.0 / N_ROCKETS)
    ct, st = math.cos(theta), math.sin(theta)
    ov, iv = [], []
    for (tang, z) in profile:
        ov.append(bm.verts.new((CX + R_OUTER*ct + tang*(-st), CY + R_OUTER*st + tang*ct, z)))
        iv.append(bm.verts.new((CX + R_INNER*ct + tang*(-st), CY + R_INNER*st + tang*ct, z)))
    bm.faces.new(ov[::-1])
    bm.faces.new(iv)
    for j in range(NP):
        nj = (j + 1) % NP
        bm.faces.new([ov[j], iv[j], iv[nj], ov[nj]])

bm.normal_update()
me = bpy.data.meshes.new("RocketCutters")
bm.to_mesh(me); bm.free(); me.update(); me.validate()
print("Cutter: %d verts, %d faces" % (len(me.vertices), len(me.polygons)))

cutter = bpy.data.objects.new("RocketCutters", me)
bpy.context.collection.objects.link(cutter)

cup = bpy.data.objects[CUP_NAME]
orig_vert_count = len(cup.data.vertices)
print("Cup before: %d verts" % orig_vert_count)

mod = cup.modifiers.new("RocketCuts", "BOOLEAN")
mod.operation = 'DIFFERENCE'
mod.object    = cutter
mod.solver    = 'EXACT'

# Apply via VIEW_3D temp_override — avoid bpy.ops for selection (context issues)
for obj in bpy.context.scene.objects:
    obj.select_set(False)
cup.select_set(True)
bpy.context.view_layer.objects.active = cup

applied = False
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        region = next((r for r in area.regions if r.type == 'WINDOW'), None)
        override = {'area': area, 'region': region, 'active_object': cup, 'selected_objects': [cup]}
        with bpy.context.temp_override(**override):
            # Ensure OBJECT mode
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            print("Mode:", bpy.context.mode, "— applying modifier...")
            bpy.ops.object.modifier_apply(modifier="RocketCuts")
        applied = True
        break

if not applied:
    raise RuntimeError("No VIEW_3D area found")

new_vert_count = len(cup.data.vertices)
print("Cup after: %d verts (was %d)" % (new_vert_count, orig_vert_count))

print("Vertex count change: %d -> %d (delta=%d)" % (orig_vert_count, new_vert_count, new_vert_count - orig_vert_count))
if new_vert_count <= orig_vert_count:
    print("WARNING: Boolean may not have cut. Continuing anyway for inspection.")


# Clean up cutter
bpy.data.objects.remove(cutter, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=r"d:\Blender\RocketCup.blend")
print("Saved RocketCup.blend")
