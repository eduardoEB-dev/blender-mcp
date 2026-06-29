import bpy, numpy as np, os

PNG_SRC = r"d:\Blender\blender-mcp\CupProjects\Images\ToInfinity.png"
OUT_DIR  = r"d:\Blender\blender-mcp\CupProjects\Images\ToInfinity_Layers"
os.makedirs(OUT_DIR, exist_ok=True)

orig = bpy.data.images.load(PNG_SRC)
W, H = orig.size
px   = np.array(orig.pixels[:], dtype=np.float32).reshape(H, W, 4)
px   = px[::-1].copy()   # flip to top-down
bpy.data.images.remove(orig)
print(f"Loaded {W}×{H}")

r, g, b, a = px[:,:,0], px[:,:,1], px[:,:,2], px[:,:,3]

# ── Diagnostic samples ────────────────────────────────────────────────────────
print("Sample pixels:")
for label, ry, rx in [
    ("black-border", 0.05, 0.50),   # top black border
    ("green-TO",     0.15, 0.50),   # "TO" text
    ("green-INF",    0.32, 0.50),   # "INFINITY"
    ("purple-AND",   0.52, 0.50),   # "AND" banner
    ("red-stripe",   0.52, 0.28),   # red chevron decoration
    ("purple-BEY",   0.72, 0.50),   # "BEYOND!"
    ("white-bg",     0.20, 0.85),   # white background
]:
    y, x = int(ry*H), int(rx*W)
    print(f"  {label:14s} ({y:3d},{x:3d}): "
          f"r={r[y,x]:.2f} g={g[y,x]:.2f} b={b[y,x]:.2f} a={a[y,x]:.2f}")

# ── Background detection ──────────────────────────────────────────────────────
# Image may have white (non-transparent) background inside the black border.
# Transparent pixels are always background; opaque near-white are also background.
bg_transparent = a < 0.15
bg_white       = (r > 0.88) & (g > 0.88) & (b > 0.88) & (a > 0.80)
background     = bg_transparent | bg_white
active         = ~background & (a > 0.15)

# ── Color detection (priority order) ─────────────────────────────────────────
# Black: very dark pixels
black = active & (r < 0.25) & (g < 0.25) & (b < 0.25)

# Lime green: high G, moderate R, very low B
green = active & ~black \
      & (g > 0.55) & (g > r * 0.85) & (b < 0.40) & (r < 0.85)

# Red: high R, low G and B — the chevron/stripe decoration on "AND" ribbon
red = active & ~black & ~green \
    & (r > 0.55) & (r > g + 0.25) & (r > b + 0.20) & (b < 0.45)

# Purple: remaining — "AND" banner + "BEYOND!" (blueish-red hue, low green)
purple = active & ~black & ~green & ~red \
       & (r > 0.20) & (b > 0.20) & (g < 0.45)

print(f"\nblack={black.sum():,}  green={green.sum():,}  "
      f"red={red.sum():,}  purple={purple.sum():,}")
missed = active & ~black & ~green & ~red & ~purple
print(f"unclassified active pixels: {missed.sum():,}")

# ── SVG helpers ───────────────────────────────────────────────────────────────
W_IN = f"{W/96:.4f}in"
H_IN = f"{H/96:.4f}in"

SVG_HDR = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    f'     width="{W_IN}" height="{H_IN}" viewBox="0 0 {W} {H}">\n'
)

def mask_to_paths(mask):
    paths = []
    for row in range(mask.shape[0]):
        in_run = False; rs = 0
        for col in range(mask.shape[1] + 1):
            on = col < mask.shape[1] and mask[row, col]
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
    # Transparent rect anchors every layer to the same bounding box in Bambu Studio
    svg = (SVG_HDR +
           f'  <rect x="0" y="0" width="{W}" height="{H}" fill="none"/>\n'
           f'  <g fill="{color_hex}" stroke="none">\n'
           f'  {path_data}\n'
           f'  </g>\n'
           f'</svg>\n')
    out = os.path.join(OUT_DIR, filename)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"  → {out}  ({os.path.getsize(out)//1024} KB, {len(paths):,} paths)")

save_svg(black,  '#1A1A1A', '01_Black.svg')
save_svg(green,  '#6DC121', '02_Green.svg')
save_svg(purple, '#5B1F7A', '03_Purple.svg')
save_svg(red,    '#D42B2B', '04_Red.svg')

print(f"\nDone — 4 SVGs in:\n{OUT_DIR}")
print("All share same viewBox — overlay all in Bambu Studio.")
