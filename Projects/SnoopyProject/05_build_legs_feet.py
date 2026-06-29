"""
Legs + feet/claws — yellow.
Convention: 1 unit = 1mm.

Two stubby legs (Z=10–25) and two feet with 3 toe claws each (Z=0–12).
Toes are separate overlapping spheres merged into each foot via boolean union.
"""
import bpy
import bmesh

YELLOW = bpy.data.materials.get("Snoopy_Yellow")

def apply_bool_union(base, cutter):
    mod = base.modifiers.new("union", 'BOOLEAN')
    mod.operation = 'UNION'
    mod.object = cutter
    mod.solver = 'FLOAT'
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier="union")
    bpy.data.objects.remove(cutter, do_unlink=True)

for side, sign in [("L", -1), ("R", 1)]:
    # --- Leg (stubby cylinder) ---
    bpy.ops.mesh.primitive_cylinder_add(
        radius=6.5,
        depth=14,
        vertices=32,
        location=(sign * 10, 2, 18)  # slight forward lean (Y=2)
    )
    leg = bpy.context.active_object
    leg.name = f"Snoopy_Leg_{side}"
    leg.scale = (1.0, 0.88, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    if YELLOW:
        leg.data.materials.append(YELLOW)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- Foot pad (oval blob) ---
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=7,
        segments=32,
        ring_count=16,
        location=(sign * 10, -2, 6)   # slightly forward of leg
    )
    foot = bpy.context.active_object
    foot.name = f"Snoopy_Foot_{side}"
    foot.scale = (1.25, 1.05, 0.85)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    if YELLOW:
        foot.data.materials.append(YELLOW)

    # --- Three toe claws ---
    # Toes fan out at front of foot (negative Y = front)
    toe_offsets = [(-4, -8, 5), (sign * 0, -9, 4.5), (4, -8, 5)]
    for j, (dx, dy, dz) in enumerate(toe_offsets):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=3.2,
            segments=16,
            ring_count=8,
            location=(sign * 10 + dx, dy, dz)
        )
        toe = bpy.context.active_object
        toe.name = f"toe_tmp_{j}"
        toe.scale = (0.95, 1.1, 0.80)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_bool_union(foot, toe)

    bpy.ops.object.select_all(action='DESELECT')
    foot.select_set(True)
    bpy.context.view_layer.objects.active = foot
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"Leg {side}: dims={[round(d,1) for d in leg.dimensions]}")
    print(f"Foot {side}: dims={[round(d,1) for d in foot.dimensions]}, Z range: {foot.bound_box[0][2]*foot.scale.z + foot.location.z:.1f}")

print("Legs & feet done.")
