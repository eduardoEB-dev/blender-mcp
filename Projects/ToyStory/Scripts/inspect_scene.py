import bpy
import numpy as np

print("=== Scene Objects ===")
for obj in bpy.data.objects:
    print(f"  {obj.name} | type={obj.type} | dims={[round(d,2) for d in obj.dimensions]}")
    bb = [obj.matrix_world @ __import__('mathutils').Vector(c) for c in obj.bound_box]
    xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
    print(f"    X: {min(xs):.2f} to {max(xs):.2f}")
    print(f"    Y: {min(ys):.2f} to {max(ys):.2f}")
    print(f"    Z: {min(zs):.2f} to {max(zs):.2f}")
