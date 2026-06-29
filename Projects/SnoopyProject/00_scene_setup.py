import bpy

# Convention: 1 Blender unit = 1mm throughout all Snoopy scripts.
# Vertex coords are written raw to 3MF with unit="millimeter".

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

print("=== Scene Cleared ===")
print(f"File: {bpy.data.filepath}")
print("Convention: 1 unit = 1mm")
print(f"Remaining objects: {len(bpy.data.objects)}")
