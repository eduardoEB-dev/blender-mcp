import bpy

# Get dimensions and center of cup
cup = bpy.data.objects['EFCooler_Cup']
dims = cup.dimensions
loc = cup.location
center_world = cup.matrix_world @ (cup.location + cup.dimensions / 2)

print("Cup dims:", tuple(round(d,2) for d in dims))
print("Cup loc:", tuple(round(d,2) for d in cup.location))

# Position camera for a clean front view of the full cup
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.overlay.show_overlays = True
                space.overlay.show_wireframes = False
                # Front view (numpad 1 equivalent)
                space.region_3d.view_perspective = 'ORTHO'
                from mathutils import Vector, Euler
                import math
                space.region_3d.view_rotation = Euler((math.radians(90), 0, 0), 'XYZ').to_quaternion()
                # Set view distance to see full cup
                space.region_3d.view_distance = 250
                space.region_3d.view_location = Vector((44, 44, 58))
        with bpy.context.temp_override(area=area):
            bpy.ops.render.opengl(write_still=True)
        break

bpy.context.scene.render.filepath = r"d:\Blender\blender-mcp\CupProjects\cup_front.png"
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        with bpy.context.temp_override(area=area):
            bpy.ops.render.opengl(write_still=True)
        break

print("done")
