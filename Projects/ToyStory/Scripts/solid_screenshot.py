import bpy

# Switch to solid shading and take screenshot
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.overlay.show_overlays = False
        break

# Use scene render output path then opengl render
bpy.context.scene.render.filepath = r"d:\Blender\blender-mcp\CupProjects\cup_solid.png"
bpy.context.scene.render.image_settings.file_format = 'PNG'

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        with bpy.context.temp_override(area=area):
            bpy.ops.render.opengl(write_still=True)
        break

print("screenshot saved")
