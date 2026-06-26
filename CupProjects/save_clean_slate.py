import bpy
# Just save as RocketCup.blend so the GUI can reload it
bpy.ops.wm.save_as_mainfile(filepath=r"d:\Blender\RocketCup.blend")
print("Saved clean slate as RocketCup.blend")
print("Verts: %d" % len(bpy.data.objects['EFCooler_Cup'].data.vertices))
