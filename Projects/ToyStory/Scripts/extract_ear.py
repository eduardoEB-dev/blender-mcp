import bpy, numpy as np, os
from collections import deque

PNG_SRC = r"d:\Blender\Images\SnoopyWSCloudsPNG.png"
OUT_DIR  = r"d:\Blender\Images\Layers"
os.makedirs(OUT_DIR, exist_ok=True)

# Tight crop around the dangling ear (adjust if needed)
# First-pass detection found content at x=330-419 y=370-608
CROP_X1, CROP_X2 = 290, 450
CROP_Y1, CROP_Y2 = 350, 630

# Load full-res image
orig = bpy.data.images.load(PNG_SRC)
W, H = orig.size
px   = np.array(orig.pixels[:], dtype=np.float32).reshape(H, W, 4)
px   = px[::-1].copy()   # Blender is bottom-up; flip to top-down
bpy.data.images.remove(orig)
print(f"Loaded {W}×{H}")

r, g, b, a = px[:,:,0], px[:,:,1], px[:,:,2], px[:,:,3]

# Work inside the crop only
cr = r[CROP_Y1:CROP_Y2, CROP_X1:CROP_X2]
cg = g[CROP_Y1:CROP_Y2, CROP_X1:CROP_X2]
cb = b[CROP_Y1:CROP_Y2, CROP_X1:CROP_X2]
ca = a[CROP_Y1:CROP_Y2, CROP_X1:CROP_X2]
ch, cw = ca.shape

# The PNG background is transparent (alpha ≈ 0).
# Opaque pixels = artwork. Non-black opaque pixels = white/fill.
# No flood fill needed — transparency already separates background from fill.
c_opaque = ca > 0.4
c_black  = (cr < 0.40) & (cg < 0.40) & (cb < 0.40) & c_opaque
c_yellow = (cr > 0.45) & (cg > 0.25) & (cb < 0.45) & (cr > cb + 0.15) & c_opaque & ~c_black
c_fill   = c_opaque & ~c_black & ~c_yellow   # white/cream interior

print(f"Crop {cw}×{ch}")
print(f"  opaque: {c_opaque.sum():,}  black: {c_black.sum():,}  fill: {c_fill.sum():,}")

# Map to full-image coordinate arrays (so SVG paths overlay on 01-03 layers)
ear_black = np.zeros((H, W), bool)
ear_white = np.zeros((H, W), bool)
ear_black[CROP_Y1:CROP_Y2, CROP_X1:CROP_X2] = c_black
ear_white[CROP_Y1:CROP_Y2, CROP_X1:CROP_X2] = c_fill

ys_b, xs_b = np.where(ear_black)
ys_w, xs_w = np.where(ear_white)
if ear_black.any():
    print(f"Ear black: {ear_black.sum():,} px  x={xs_b.min()}-{xs_b.max()} y={ys_b.min()}-{ys_b.max()}")
if ear_white.any():
    print(f"Ear white: {ear_white.sum():,} px  x={xs_w.min()}-{xs_w.max()} y={ys_w.min()}-{ys_w.max()}")
else:
    print("WARNING: no white fill detected — ear may be solid black in the original PNG")

# SVG helpers (same viewBox as 01-03 so they overlay correctly)
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
                paths.append(f"M {rs},{row} L {col},{row} L {col},{row+1} L {rs},{row+1} Z")
    return paths

SVG_HEADER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    '     width="20.75in" height="14.625in" viewBox="0 0 1494 1053">\n'
)

def save_svg(mask, color_hex, filename):
    paths = mask_to_paths(mask)
    if not paths:
        print(f"  (skipping {filename} — no pixels)")
        return
    path_data = '\n  '.join(f'<path d="{d}"/>' for d in paths)
    svg = (
        SVG_HEADER +
        f'  <title>{filename}</title>\n'
        f'  <g fill="{color_hex}" stroke="none">\n'
        f'  {path_data}\n'
        f'  </g>\n'
        f'</svg>\n'
    )
    out = os.path.join(OUT_DIR, filename + '.svg')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"  → {out}  ({os.path.getsize(out)//1024} KB, {len(paths):,} paths)")

save_svg(ear_black, '#000000', '04_Ear_Black')
save_svg(ear_white, '#FFFFFF', '05_Ear_White')
print("Done.")
