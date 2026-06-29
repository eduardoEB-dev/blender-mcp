import bpy, numpy as np, os
from collections import deque

PNG_SRC = r"d:\Blender\blender-mcp\CupProjects\Images\Toy_Story_Layers\buzzBadge.png"
OUT_DIR  = r"d:\Blender\blender-mcp\CupProjects\Images\Toy_Story_Layers\Buzz_SVGs\Buzz_Badge"
os.makedirs(OUT_DIR, exist_ok=True)

# Exclude "STAR COMMAND" text — keep top 70% of image height
CROP_Y_FRAC = 0.70

orig = bpy.data.images.load(PNG_SRC)
W, H = orig.size
px   = np.array(orig.pixels[:], dtype=np.float32).reshape(H, W, 4)
px   = px[::-1].copy()   # flip to top-down
bpy.data.images.remove(orig)
print(f"Loaded {W}×{H}  crop: top {int(H*CROP_Y_FRAC)} rows")

r, g, b, a = px[:,:,0], px[:,:,1], px[:,:,2], px[:,:,3]

# Crop mask (zero out the STAR COMMAND text rows)
crop = np.zeros((H, W), bool)
crop[:int(H * CROP_Y_FRAC), :] = True
opaque = (a > 0.15) & crop   # PNG likely has transparent background

# ── Diagnostic: sample key regions ──────────────────────────────────────────
print("Sample pixels:")
for label, ry, rx in [
    ("wing-L",    0.30, 0.12),   # left wing body
    ("wing-R",    0.30, 0.78),   # right wing body
    ("circ-left", 0.38, 0.38),   # left of rocket (dark ring)
    ("circ-rgt",  0.38, 0.62),   # right of rocket (dark ring)
    ("rocket",    0.28, 0.50),   # rocket center (white)
    ("outline-T", 0.10, 0.50),   # top edge of badge (black)
    ("bg-corner", 0.02, 0.02),   # transparent background
]:
    y, x = int(ry*H), int(rx*W)
    print(f"  {label:12s} ({y:3d},{x:3d}): "
          f"r={r[y,x]:.2f} g={g[y,x]:.2f} b={b[y,x]:.2f} a={a[y,x]:.2f}")

brightness = r + g + b   # sum, range 0-3

# ── Color detection ──────────────────────────────────────────────────────────
# Priority: black → white → dark_blue → light_blue (catch-all blue)

black = opaque & (r < 0.28) & (g < 0.28) & (b < 0.32)

# White: rocket body — very bright, nearly equal R/G/B
white = opaque & ~black & (r > 0.82) & (g > 0.82) & (b > 0.80)

# Dark blue: orbital ring + deep shadows — blue-dominant AND distinctly dark
# Key: brightness sum < 1.55  (avg < 0.517) separates dark ring from wing periwinkle
dark_blue = opaque & ~black & ~white \
          & (b > 0.38) & (b > r + 0.10) \
          & (brightness < 1.60)

# Light blue: main wing periwinkle — blue-dominant but brighter (brightness >= 1.60)
light_blue = opaque & ~black & ~white & ~dark_blue \
           & (b > 0.55)

print(f"\nblack={black.sum():,}  white={white.sum():,}  "
      f"dark_blue={dark_blue.sum():,}  light_blue={light_blue.sum():,}")

missed = opaque & ~black & ~white & ~dark_blue & ~light_blue
print(f"unclassified opaque pixels: {missed.sum():,}")

# ── SVG helpers ──────────────────────────────────────────────────────────────
W_IN = f"{W/96:.4f}in"
H_IN = f"{H/96:.4f}in"

SVG_HEADER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    f'     width="{W_IN}" height="{H_IN}" viewBox="0 0 {W} {H}">\n'
)

def mask_to_paths(mask):
    h, w = mask.shape
    paths = []
    for row in range(h):
        in_run = False; rs = 0
        for col in range(w + 1):
            on = col < w and mask[row, col]
            if on and not in_run:
                in_run = True; rs = col
            elif not on and in_run:
                in_run = False
                paths.append(
                    f"M {rs},{row} L {col},{row} L {col},{row+1} L {rs},{row+1} Z"
                )
    return paths

def save_svg(mask, color_hex, filename):
    print(f"Building {filename}...")
    paths = mask_to_paths(mask)
    path_data = '\n  '.join(f'<path d="{d}"/>' for d in paths)
    svg = (
        SVG_HEADER +
        f'  <g fill="{color_hex}" stroke="none">\n'
        f'  {path_data}\n'
        f'  </g>\n'
        f'</svg>\n'
    )
    out = os.path.join(OUT_DIR, filename)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"  → {out}  ({os.path.getsize(out)//1024} KB, {len(paths):,} paths)")

save_svg(black,      '#1A1A1A', '01_Black_Outline.svg')
save_svg(dark_blue,  '#3D5A8A', '02_Dark_Blue.svg')
save_svg(light_blue, '#8B9FD4', '03_Light_Blue.svg')
save_svg(white,      '#FFFFFF', '04_White.svg')

print(f"\nDone — 4 SVGs in:\n{OUT_DIR}")
print("All share the same viewBox — overlay all in Bambu Studio.")
