import bpy

scene = bpy.context.scene

# Remove old preview camera/light if present
for name in ['PreviewCam','Sun']:
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

# Camera directly in front of the cup (-Y direction, looking at +Y)
# Cup front face center: X≈45, Y≈-42, Z≈85  (from geometry inspection)
import math
cam_data = bpy.data.cameras.new("PreviewCam")
cam = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (45, -250, 85)           # straight in front, centered on artwork
cam.rotation_euler = (math.radians(90), 0, 0)  # looking straight in +Y direction
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 120              # tight crop on the cup face
scene.camera = cam

# Key light from front-left
light_data = bpy.data.lights.new("Sun", 'SUN')
light_data.energy = 3
light = bpy.data.objects.new("Sun", light_data)
bpy.context.collection.objects.link(light)
light.location = (0, -200, 150)
light.rotation_euler = (math.radians(45), 0, math.radians(-30))

# Cup material
cup = bpy.data.objects.get('EFCooler_Cup')
if cup:
    if not cup.data.materials:
        m = bpy.data.materials.new("CupGray")
        m.diffuse_color = (0.5, 0.5, 0.5, 1)
        cup.data.materials.append(m)

scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 700
scene.render.resolution_y = 900
scene.render.filepath = r"d:\Blender\Images\preview_front.png"
scene.render.image_settings.file_format = 'PNG'

bpy.ops.render.render(write_still=True)
print("Rendered to preview_front.png")
