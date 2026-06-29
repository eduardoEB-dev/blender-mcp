"""
Snoopy head — white, large rounded sphere.
Convention: 1 unit = 1mm.

Figure layout (Z-axis, bottom to top):
  0–10   feet/claws
  10–25  legs
  25–68  dino body
  68–74  neck connector zone
  74–100 head  (sphere radius=15, center Z=82 → bottom=67, top=97 + ~3mm crochet bumps)
"""
import bpy
import bmesh

def make_material(name, rgba):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.85
    return mat

# --- shared materials (create once, reuse across scripts) ---
WHITE  = make_material("Snoopy_White",  (0.95, 0.95, 0.95, 1.0))
BLACK  = make_material("Snoopy_Black",  (0.05, 0.05, 0.05, 1.0))
BLUE   = make_material("Snoopy_Blue",   (0.04, 0.32, 0.82, 1.0))
YELLOW = make_material("Snoopy_Yellow", (0.95, 0.72, 0.04, 1.0))

# --- Head ---
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=15,
    segments=96,
    ring_count=48,
    location=(0, 0, 82)
)
head = bpy.context.active_object
head.name = "Snoopy_Head"

# Slightly oval: a touch taller (Z), slightly shallower front-to-back (Y)
head.scale = (1.0, 0.90, 1.08)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Smooth shading
bpy.ops.object.shade_smooth()

# Material
head.data.materials.append(WHITE)

# UV unwrap (sphere projection)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.sphere_project()
bpy.ops.object.mode_set(mode='OBJECT')

dims = head.dimensions
bb = [head.matrix_world @ __import__('mathutils').Vector(c) for c in head.bound_box]
zs = [v.z for v in bb]
print(f"Head created: {head.name}")
print(f"  Dimensions (mm): {[round(d,2) for d in dims]}")
print(f"  Z range: {min(zs):.1f} → {max(zs):.1f}")
