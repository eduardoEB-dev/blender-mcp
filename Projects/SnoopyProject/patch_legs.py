"""
Patch: replace coarse leg cylinders with denser ones (depth_segments=8).
Re-applies crochet displacement so bumps are visible in Z direction.
"""
import bpy, bmesh, math, numpy as np

YELLOW = bpy.data.materials.get("Snoopy_Yellow")
tex    = bpy.data.textures.get("CrochetTex")

STITCH_MM     = 3.0
BUMPS_PER_ROW = 16
DISP_STR      = 1.5

def calc_uv(obj):
    return math.pi * max(obj.dimensions) / (STITCH_MM * BUMPS_PER_ROW)

def scale_uvs(obj, s):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    if uv:
        for f in bm.faces:
            for l in f.loops:
                l[uv].uv.x = (l[uv].uv.x - 0.5)*s + 0.5
                l[uv].uv.y = (l[uv].uv.y - 0.5)*s + 0.5
    bm.to_mesh(obj.data); obj.data.update(); bm.free()

def select_active(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active = o

for side, sign in [("L",-1),("R",1)]:
    old = bpy.data.objects.get(f"Snoopy_Leg_{side}")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    # Build cylinder with 9 rings (8 segments in Z) via bmesh so crochet bumps show
    R=6.5; SEGS=32; RINGS=9; H=14
    mesh = bpy.data.meshes.new(f"Snoopy_Leg_{side}")
    obj  = bpy.data.objects.new(f"Snoopy_Leg_{side}", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    rows=[]
    for ri in range(RINGS):
        z = -H/2 + ri * H/(RINGS-1)
        row=[]
        for si in range(SEGS):
            ang = 2*math.pi*si/SEGS
            row.append(bm.verts.new((R*math.cos(ang), R*math.sin(ang), z)))
        rows.append(row)
    for ri in range(RINGS-1):
        for si in range(SEGS):
            sn=(si+1)%SEGS
            bm.faces.new([rows[ri][si],rows[ri][sn],rows[ri+1][sn],rows[ri+1][si]])
    bc=bm.verts.new((0,0,-H/2))
    tc=bm.verts.new((0,0, H/2))
    for si in range(SEGS):
        sn=(si+1)%SEGS
        bm.faces.new([bc, rows[0][sn],  rows[0][si]])
        bm.faces.new([tc, rows[-1][si], rows[-1][sn]])
    bm.normal_update(); bm.to_mesh(mesh); mesh.update(); bm.free()

    obj.location=(sign*10, 2, 18)
    obj.scale=(1.0, 0.88, 1.0)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.ops.object.shade_smooth()
    if YELLOW: obj.data.materials.append(YELLOW)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    leg = obj

    # Apply crochet
    select_active(leg)
    scale_uvs(leg, calc_uv(leg))
    if tex:
        ms = leg.modifiers.new("SubdTmp","SUBSURF")
        ms.levels=1; ms.subdivision_type='CATMULL_CLARK'
        bpy.ops.object.modifier_apply(modifier="SubdTmp")
        md = leg.modifiers.new("Crochet","DISPLACE")
        md.texture=tex; md.strength=DISP_STR; md.mid_level=0.5
        md.texture_coords='UV'; md.direction='NORMAL'
        bpy.ops.object.modifier_apply(modifier="Crochet")

    print(f"Leg {side}: {len(leg.data.vertices):,} verts, dims={[round(d,1) for d in leg.dimensions]}")

bpy.ops.wm.save_mainfile()
print("Legs patched and saved.")
