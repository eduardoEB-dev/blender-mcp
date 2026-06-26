"""
Dino back spines — 5 yellow pointed fins running up the back.
Convention: 1 unit = 1mm.

Spines sit on the back of the body (positive Y side).
They run from upper-back (Z≈58) up behind the neck (Z≈78).
Each spine = flattened sphere, stretched tall, then sharpened by non-uniform scale.
"""
import bpy
import math

YELLOW = bpy.data.materials.get("Snoopy_Yellow")

# (z_center, scale_x, scale_y, scale_z)  — base sphere radius=6
SPINE_DEFS = [
    (58,  1.55, 0.55, 1.20),   # bottom spine (widest)
    (63,  1.40, 0.50, 1.45),
    (68,  1.20, 0.45, 1.55),   # mid (tallest)
    (73,  1.00, 0.40, 1.40),
    (78,  0.80, 0.38, 1.15),   # top spine (smallest)
]

for i, (z, sx, sy, sz) in enumerate(SPINE_DEFS):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=6,
        segments=32,
        ring_count=16,
        location=(0, 17, z)   # Y=17 puts spine behind body surface (~Y=17.6 at equator)
    )
    spine = bpy.context.active_object
    spine.name = f"Snoopy_Spine_{i+1:02d}"
    spine.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()

    if YELLOW:
        spine.data.materials.append(YELLOW)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.sphere_project()
    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"Spine {i+1}: dims={[round(d,1) for d in spine.dimensions]}, Z={z}")

print("Spines done.")
