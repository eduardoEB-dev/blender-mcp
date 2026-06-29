"""
Ears: two long floppy black shapes hanging from top-sides of head.
Nose: black oval button on front of head.
Convention: 1 unit = 1mm.

Head center: (0, 0, 82). Head radii approx: X=15, Y=13.5, Z=16.2
"""
import bpy
import bmesh
import math

BLACK = bpy.data.materials.get("Snoopy_Black")

# ---------- EARS ----------
# Each ear: elongated sphere, ~14mm wide, 9mm deep, 26mm tall
# Attached near top-side of head, hanging straight down with slight angle
EAR_RX = 7.0   # half-width  (X)
EAR_RY = 4.5   # half-depth  (Y)  -- floppy ears are thin
EAR_RZ = 13.0  # half-height (Z)

for side, sign in [("L", -1), ("R", 1)]:
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=EAR_RZ,          # base radius; we'll scale non-uniformly
        segments=48,
        ring_count=24,
        location=(sign * 14.5, -1.5, 80)
    )
    ear = bpy.context.active_object
    ear.name = f"Snoopy_Ear_{side}"

    # Scale to proper ear proportions
    ear.scale = (EAR_RX / EAR_RZ, EAR_RY / EAR_RZ, 1.0)
    # Tilt top of ear slightly outward (±5°)
    ear.rotation_euler[1] = math.radians(sign * 5)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    bpy.ops.object.shade_smooth()

    if BLACK:
        ear.data.materials.append(BLACK)

    # UV unwrap
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.sphere_project()
    bpy.ops.object.mode_set(mode='OBJECT')

    dims = ear.dimensions
    print(f"Ear {side}: dims={[round(d,1) for d in dims]}, loc={[round(c,1) for c in ear.location]}")

# ---------- NOSE ----------
# Oval black disc on the front face of the head.
# Head front surface at Y ≈ -13.5 at Z=82, nose sits lower at Z≈76
# Model as a flattened sphere (disc-like)
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=5.5,
    segments=32,
    ring_count=16,
    location=(0, -13.5, 76)   # front of head, lower area
)
nose = bpy.context.active_object
nose.name = "Snoopy_Nose"
# Flatten in Y (depth) to make it a button/disc
nose.scale = (1.0, 0.45, 0.75)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()

if BLACK:
    nose.data.materials.append(BLACK)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.sphere_project()
bpy.ops.object.mode_set(mode='OBJECT')

print(f"Nose: dims={[round(d,1) for d in nose.dimensions]}, loc={[round(c,1) for c in nose.location]}")
print("Ears & nose done.")
