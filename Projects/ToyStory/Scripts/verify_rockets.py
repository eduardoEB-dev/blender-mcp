import bpy
cup = bpy.data.objects['EFCooler_Cup']
print("Verts: %d" % len(cup.data.vertices))
# Check for non-convex faces (rocket indentations would create them)
import math
CX, CY = 43.94, 44.45
# sample some vertices at grip band Z boundary
low = [(v.co.x, v.co.y, v.co.z) for v in cup.data.vertices if 40 < v.co.z < 42]
high = [(v.co.x, v.co.y, v.co.z) for v in cup.data.vertices if 73 < v.co.z < 75]
print("Verts at grip bottom (Z 40-42): %d" % len(low))
print("Verts at grip top (Z 73-75): %d" % len(high))
# Sample a few verts at rocket z range
inner = [(v.co.x, v.co.y, v.co.z) for v in cup.data.vertices if 45 < v.co.z < 55]
print("Verts between grip boundaries (Z 45-55): %d" % len(inner))
if inner:
    rs = [math.sqrt((x-CX)**2+(y-CY)**2) for x,y,z in inner[:20]]
    print("  Sample radii:", [round(r,2) for r in rs[:10]])
