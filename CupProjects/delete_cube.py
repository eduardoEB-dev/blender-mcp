import bpy

# List all objects before deletion
print("Objects in scene:", [obj.name for obj in bpy.data.objects])

# Find and delete any object named "Cube" (or mesh cube)
cubes = [obj for obj in bpy.data.objects if obj.name == "Cube" or (obj.type == 'MESH' and obj.name.startswith("Cube"))]
print("Cubes found:", [c.name for c in cubes])

bpy.ops.object.select_all(action='DESELECT')
for cube in cubes:
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube

bpy.ops.object.delete()

print("Objects after deletion:", [obj.name for obj in bpy.data.objects])

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("File saved.")
