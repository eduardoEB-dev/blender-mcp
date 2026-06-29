"""
Neck collar — white, bridges head (Z=66) and body (Z=65) with a visible ring.
Convention: 1 unit = 1mm.

The neck is a short ring/collar that sits between head and body.
It will receive D-profile connectors on top (→ head) and bottom (→ body)
in a later script. For now, basic geometry only.
"""
import bpy

WHITE = bpy.data.materials.get("Snoopy_White")

# Torus-like neck ring: outer radius 12mm, inner hollow for connector space
# Built as a short cylinder (tube) using two concentric cylinders or just a solid disc
# For printing: solid short cylinder is simplest and most robust
bpy.ops.mesh.primitive_cylinder_add(
    radius=11,
    depth=7,
    vertices=64,
    location=(0, 0, 68)   # sits between body top (Z=65) and head bottom (Z=66)
)
neck = bpy.context.active_object
neck.name = "Snoopy_Neck"
neck.scale = (1.0, 0.90, 1.0)   # slightly oval to match head's Y compression
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()

if WHITE:
    neck.data.materials.append(WHITE)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode='OBJECT')

bb = [neck.matrix_world @ __import__('mathutils').Vector(c) for c in neck.bound_box]
zs = [v.z for v in bb]
print(f"Neck: dims={[round(d,1) for d in neck.dimensions]}")
print(f"  Z range: {min(zs):.1f} → {max(zs):.1f}")
