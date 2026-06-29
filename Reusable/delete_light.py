import bpy

lights = [obj for obj in bpy.data.objects if obj.type == 'LIGHT']
print("Lights found:", [l.name for l in lights])

bpy.ops.object.select_all(action='DESELECT')
for light in lights:
    light.select_set(True)
    bpy.context.view_layer.objects.active = light

bpy.ops.object.delete()

print("Objects after deletion:", [obj.name for obj in bpy.data.objects])
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("File saved.")
