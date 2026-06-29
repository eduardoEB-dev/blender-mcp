import bpy

cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
print("Cameras found:", [c.name for c in cameras])

bpy.ops.object.select_all(action='DESELECT')
for cam in cameras:
    cam.select_set(True)
    bpy.context.view_layer.objects.active = cam

bpy.ops.object.delete()

print("Objects after deletion:", [obj.name for obj in bpy.data.objects])
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("File saved.")
