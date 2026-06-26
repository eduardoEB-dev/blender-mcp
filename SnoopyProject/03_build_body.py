"""
Dino body/shell — blue, fat egg shape.
Convention: 1 unit = 1mm.

Layout:
  Body center Z=45, radius ~20 → Z=25–65 (40mm tall, 42mm wide, 35mm deep).
  Head bottom sits at Z≈66, so body top at Z=65 leaves a 1mm gap for neck zone.
  Legs attach at bottom (Z=25).
"""
import bpy

BLUE = bpy.data.materials.get("Snoopy_Blue")

bpy.ops.mesh.primitive_uv_sphere_add(
    radius=20,
    segments=96,
    ring_count=48,
    location=(0, 0, 45)
)
body = bpy.context.active_object
body.name = "Snoopy_Body"

# Fat egg: wider left-right, slightly shallower front-back, natural Z
body.scale = (1.05, 0.88, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()

if BLUE:
    body.data.materials.append(BLUE)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.sphere_project()
bpy.ops.object.mode_set(mode='OBJECT')

bb = [body.matrix_world @ __import__('mathutils').Vector(c) for c in body.bound_box]
zs = [v.z for v in bb]
print(f"Body: dims={[round(d,1) for d in body.dimensions]}")
print(f"  Z range: {min(zs):.1f} → {max(zs):.1f}")
