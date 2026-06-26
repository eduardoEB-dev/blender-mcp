"""
Generate crochet bump image via numpy and bake it as displacement geometry
onto all Snoopy parts. Convention: 1 unit = 1mm.

Stitch target: ~3mm per stitch, ~1.5mm total bump height (valley→peak).
"""
import bpy
import bmesh
import numpy as np
import math

# ============================================================
# A. GENERATE CROCHET BUMP IMAGE
# ============================================================
SIZE         = 512
BUMPS_PER_ROW = 16        # bumps across one full image width
CELL_W       = SIZE / BUMPS_PER_ROW          # pixels per stitch width
CELL_H       = CELL_W * 0.80                 # stitches slightly wider than tall
SHARPNESS    = 1.6                           # bump profile exponent (higher = pointier)

print(f"Generating {SIZE}×{SIZE} crochet image ({BUMPS_PER_ROW} bumps/row)...")

y_g, x_g = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
img_arr   = np.zeros((SIZE, SIZE), dtype=np.float32)

n_rows = int(SIZE / CELL_H) + 3
n_cols = int(SIZE / CELL_W) + 3

for row in range(-1, n_rows):
    for col in range(-1, n_cols):
        # Brick-pattern offset: alternate rows shift half a stitch
        cx = (col + 0.5 + (row % 2) * 0.5) * CELL_W
        cy = (row + 0.5) * CELL_H
        rx = CELL_W * 0.46
        ry = CELL_H * 0.46
        nx = (x_g - cx) / rx
        ny = (y_g - cy) / ry
        r2 = nx*nx + ny*ny
        bump = np.where(r2 < 1.0, (1.0 - r2)**SHARPNESS, 0.0).astype(np.float32)
        img_arr = np.maximum(img_arr, bump)

print(f"  Image: max={img_arr.max():.3f}, mean={img_arr.mean():.3f}")

# Load into Blender image datablock
old = bpy.data.images.get("CrochetBumps")
if old:
    bpy.data.images.remove(old)
img = bpy.data.images.new("CrochetBumps", width=SIZE, height=SIZE,
                           alpha=False, float_buffer=True)
# Blender stores pixels bottom-up → flip vertically
bump_flip = np.flipud(img_arr)
rgba = np.stack([bump_flip, bump_flip, bump_flip,
                 np.ones_like(bump_flip)], axis=-1).ravel()
img.pixels[:] = rgba.tolist()
img.pack()
print(f"  Image '{img.name}' packed into .blend")

# Create Displace modifier texture
old_tex = bpy.data.textures.get("CrochetTex")
if old_tex:
    bpy.data.textures.remove(old_tex)
tex = bpy.data.textures.new("CrochetTex", 'IMAGE')
tex.image = img
tex.extension = 'REPEAT'

# ============================================================
# B. APPLY DISPLACEMENT TO EACH PART
# ============================================================
STITCH_MM    = 3.0    # target stitch size in mm
DISP_STRENGTH = 1.5   # mm from mid-level to peak (valley→peak = 3mm)

def calc_uv_scale(obj):
    """UV tiles needed so one stitch = STITCH_MM mm."""
    max_dim = max(obj.dimensions)
    circum  = math.pi * max_dim            # approximate circumference
    return circum / (STITCH_MM * BUMPS_PER_ROW)

def scale_uvs(obj, scale):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        bm.free()
        return
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer].uv
            uv.x = (uv.x - 0.5) * scale + 0.5
            uv.y = (uv.y - 0.5) * scale + 0.5
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()

# (object_name, subdivision_level_before_disp)
PARTS = [
    ("Snoopy_Head",     1),
    ("Snoopy_Ear_L",    1),
    ("Snoopy_Ear_R",    1),
    ("Snoopy_Nose",     0),
    ("Snoopy_Body",     1),
    ("Snoopy_Neck",     1),
    ("Snoopy_Leg_L",    1),
    ("Snoopy_Leg_R",    1),
    ("Snoopy_Foot_L",   1),
    ("Snoopy_Foot_R",   1),
    ("Snoopy_Spine_01", 1),
    ("Snoopy_Spine_02", 1),
    ("Snoopy_Spine_03", 1),
    ("Snoopy_Spine_04", 1),
    ("Snoopy_Spine_05", 1),
]

for name, subd in PARTS:
    obj = bpy.data.objects.get(name)
    if obj is None:
        print(f"  SKIP (missing): {name}")
        continue

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    uv_s = calc_uv_scale(obj)
    scale_uvs(obj, uv_s)

    if subd > 0:
        m = obj.modifiers.new("SubdTmp", "SUBSURF")
        m.levels = subd
        m.render_levels = subd
        m.subdivision_type = 'CATMULL_CLARK'
        bpy.ops.object.modifier_apply(modifier="SubdTmp")

    m = obj.modifiers.new("Crochet", "DISPLACE")
    m.texture       = tex
    m.strength      = DISP_STRENGTH
    m.mid_level     = 0.5
    m.texture_coords = 'UV'
    m.direction     = 'NORMAL'
    bpy.ops.object.modifier_apply(modifier="Crochet")

    vc = len(obj.data.vertices)
    print(f"  {name}: uv_scale={uv_s:.2f}, verts={vc:,}, subd={subd}")

# ============================================================
# C. SAVE
# ============================================================
bpy.ops.wm.save_mainfile()
print("\nCrochet applied and file saved.")
for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    print(f"  {obj.name}: {len(obj.data.vertices):,} verts")
