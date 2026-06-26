"""Remove default scene objects, duplicate .001 objects, and leftover temp objects."""
import bpy

to_remove = []
for obj in bpy.data.objects:
    name = obj.name
    if name in ('Camera', 'Cube', 'Light'):
        to_remove.append(obj)
    elif '.001' in name:
        to_remove.append(obj)
    elif name.startswith('toe_tmp'):
        to_remove.append(obj)

for obj in to_remove:
    print(f"  Removing: {obj.name}")
    bpy.data.objects.remove(obj, do_unlink=True)

print(f"\nRemaining objects ({len(bpy.data.objects)}):")
for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    print(f"  {obj.name}")
