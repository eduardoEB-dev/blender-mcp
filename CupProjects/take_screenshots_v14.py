import bpy, math
from mathutils import Vector, Euler

CX, CY = 43.94, 44.45

scene = bpy.context.scene
scene.render.image_settings.file_format = 'PNG'

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.overlay.show_overlays = False
        break

def shoot(filepath, view_rot, dist, loc):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.region_3d.view_perspective = 'PERSP'
                    space.region_3d.view_rotation = view_rot
                    space.region_3d.view_distance = dist
                    space.region_3d.view_location = Vector(loc)
            scene.render.filepath = filepath
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            with bpy.context.temp_override(area=area, region=region):
                bpy.ops.render.opengl(write_still=True)
            break

# Angle view — looking at grip band from front-left
r1 = Euler((math.radians(70), 0, math.radians(-35)), 'XYZ').to_quaternion()
shoot(r'd:\Blender\blender-mcp\CupProjects\v14_angle.png', r1, 120, (CX, CY, 57))

# Bottom of rockets
r2 = Euler((math.radians(85), 0, math.radians(-10)), 'XYZ').to_quaternion()
shoot(r'd:\Blender\blender-mcp\CupProjects\v14_bottom.png', r2, 80, (CX, CY, 45))

# Wide view of grip band
r3 = Euler((math.radians(75), 0, math.radians(-20)), 'XYZ').to_quaternion()
shoot(r'd:\Blender\blender-mcp\CupProjects\v14_wide.png', r3, 200, (CX, CY, 57))

print("Screenshots done")
