import bpy
import numpy as np

cup = bpy.data.objects['EFCooler_Cup']
n = len(cup.data.vertices)

coords = np.zeros(n * 3, dtype=np.float32)
cup.data.vertices.foreach_get('co', coords)
z_all = coords[2::3]  # every 3rd value starting at index 2
z_sorted = np.sort(z_all)

print("Total verts: %d" % n)
print("Z min=%.4f max=%.4f" % (z_sorted[0], z_sorted[-1]))

# Show Z values around the expected grip band (indices 24000-28000)
mid = n // 2
print("\nZ values at indices %d-%d (around 50th pct):" % (mid-5, mid+5))
for i in range(mid-5, mid+6):
    print("  [%d] Z=%.4f" % (i, z_sorted[i]))

# Find all unique Z values in range 35-80
in_range = z_sorted[(z_sorted >= 35) & (z_sorted <= 80)]
print("\nAll Z values in [35, 80]: count=%d" % len(in_range))
if len(in_range) > 0:
    uniq = np.unique(np.round(in_range, 2))
    print("Unique (rounded to 0.01mm):", uniq[:30].tolist())
else:
    # Show what the boundary actually is
    below = z_sorted[z_sorted < 42.5]
    above = z_sorted[z_sorted > 71.5]
    print("  Max Z below 42.5: %.4f" % (below[-1] if len(below) else -1))
    print("  Min Z above 71.5: %.4f" % (above[0] if len(above) else -1))
