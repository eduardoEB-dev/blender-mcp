"""
Runs all part-building scripts in sequence and saves the file.
Convention: 1 unit = 1mm.
"""
import bpy
import bmesh
import math

# ============================================================
# 0. CLEAR SCENE
# ============================================================
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh, do_unlink=True)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat, do_unlink=True)
for tex in list(bpy.data.textures):
    bpy.data.textures.remove(tex, do_unlink=True)
for img in list(bpy.data.images):
    bpy.data.images.remove(img, do_unlink=True)
print("Scene cleared.")

# ============================================================
# 1. MATERIALS
# ============================================================
def make_mat(name, rgba):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.85
    return mat

WHITE  = make_mat("Snoopy_White",  (0.95, 0.95, 0.95, 1.0))
BLACK  = make_mat("Snoopy_Black",  (0.05, 0.05, 0.05, 1.0))
BLUE   = make_mat("Snoopy_Blue",   (0.04, 0.32, 0.82, 1.0))
YELLOW = make_mat("Snoopy_Yellow", (0.95, 0.72, 0.04, 1.0))

def uv_sphere(name, radius, loc, segs, rings, mat, scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segs,
                                          ring_count=rings, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.sphere_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj

# ============================================================
# 2. HEAD  (white, radius 15, center Z=82)
# ============================================================
head = uv_sphere("Snoopy_Head", 15, (0,0,82), 96, 48, WHITE, (1.0, 0.90, 1.08))
bb = [head.matrix_world @ __import__('mathutils').Vector(c) for c in head.bound_box]
print(f"Head: {[round(d,1) for d in head.dimensions]}  Z={min(v.z for v in bb):.1f}–{max(v.z for v in bb):.1f}")

# ============================================================
# 3. EARS  (black, floppy, left & right)
# ============================================================
for side, sign in [("L",-1),("R",1)]:
    ear = uv_sphere(f"Snoopy_Ear_{side}", 13, (sign*14.5,-1.5,80), 48, 24,
                    BLACK, (7.0/13.0, 4.5/13.0, 1.0))
    ear.rotation_euler[1] = math.radians(sign * 5)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    print(f"Ear {side}: {[round(d,1) for d in ear.dimensions]}")

# ============================================================
# 4. NOSE  (black oval button on front of head)
# ============================================================
nose = uv_sphere("Snoopy_Nose", 5.5, (0,-13.5,76), 32, 16, BLACK, (1.0, 0.45, 0.75))
print(f"Nose: {[round(d,1) for d in nose.dimensions]}")

# ============================================================
# 5. BODY  (blue, fat egg, Z=25–65)
# ============================================================
body = uv_sphere("Snoopy_Body", 20, (0,0,45), 96, 48, BLUE, (1.05, 0.88, 1.0))
print(f"Body: {[round(d,1) for d in body.dimensions]}")

# ============================================================
# 6. NECK  (white collar, Z=64.5–71.5)
# ============================================================
bpy.ops.mesh.primitive_cylinder_add(radius=11, depth=7, vertices=64, location=(0,0,68))
neck = bpy.context.active_object
neck.name = "Snoopy_Neck"
neck.scale = (1.0, 0.90, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()
neck.data.materials.append(WHITE)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode='OBJECT')
print(f"Neck: {[round(d,1) for d in neck.dimensions]}")

# ============================================================
# 7. SPINES  (yellow, 5 fins on back)
# ============================================================
SPINE_DEFS = [
    (58, 1.55, 0.55, 1.20),
    (63, 1.40, 0.50, 1.45),
    (68, 1.20, 0.45, 1.55),
    (73, 1.00, 0.40, 1.40),
    (78, 0.80, 0.38, 1.15),
]
for i,(z,sx,sy,sz) in enumerate(SPINE_DEFS):
    sp = uv_sphere(f"Snoopy_Spine_{i+1:02d}", 6, (0,17,z), 32, 16, YELLOW, (sx,sy,sz))
    print(f"Spine {i+1}: {[round(d,1) for d in sp.dimensions]}")

# ============================================================
# 8. LEGS + FEET  (yellow)
# ============================================================
def apply_bool_union(base, cutter):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = base
    base.select_set(True)
    mod = base.modifiers.new("union_tmp", 'BOOLEAN')
    mod.operation = 'UNION'
    mod.object = cutter
    mod.solver = 'FLOAT'
    bpy.ops.object.modifier_apply(modifier="union_tmp")
    bpy.data.objects.remove(cutter, do_unlink=True)

for side, sign in [("L",-1),("R",1)]:
    # Leg
    bpy.ops.mesh.primitive_cylinder_add(radius=6.5, depth=14, vertices=32,
                                         location=(sign*10, 2, 18))
    leg = bpy.context.active_object
    leg.name = f"Snoopy_Leg_{side}"
    leg.scale = (1.0, 0.88, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    leg.data.materials.append(YELLOW)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Foot pad
    bpy.ops.mesh.primitive_uv_sphere_add(radius=7, segments=32, ring_count=16,
                                          location=(sign*10, -2, 6))
    foot = bpy.context.active_object
    foot.name = f"Snoopy_Foot_{side}"
    foot.scale = (1.25, 1.05, 0.85)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    foot.data.materials.append(YELLOW)

    # Three toe claws
    toe_offsets = [(-4,-8,5), (0,-9,4.5), (4,-8,5)]
    for j,(dx,dy,dz) in enumerate(toe_offsets):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=3.2, segments=16, ring_count=8,
                                              location=(sign*10+dx, dy, dz))
        toe = bpy.context.active_object
        toe.name = f"toe_tmp_{j}"
        toe.scale = (0.95, 1.10, 0.80)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_bool_union(foot, toe)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = foot
    foot.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"Leg {side}: {[round(d,1) for d in leg.dimensions]}")
    print(f"Foot {side}: {[round(d,1) for d in foot.dimensions]}")

# ============================================================
# 9. SAVE
# ============================================================
bpy.ops.wm.save_mainfile()
print("\n=== All parts built and saved ===")
print(f"Total objects: {len(bpy.data.objects)}")
for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    print(f"  {obj.name}  {[round(d,1) for d in obj.dimensions]}")
