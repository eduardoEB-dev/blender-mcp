import bpy, numpy as np, os

PNG_SRC = r"d:\Blender\Images\Toy_Story_logo.svg.png"
OUT_DIR  = r"d:\Blender\Images\Toy_Story_Layers"
os.makedirs(OUT_DIR, exist_ok=True)

# Load image
orig = bpy.data.images.load(PNG_SRC)
W, H = orig.size
px = np.array(orig.pixels[:], dtype=np.float32).reshape(H, W, 4)
px = px[::-1].copy()   # Blender is bottom-up; flip to top-down
bpy.data.images.remove(orig)
print(f"Loaded {W}×{H}")

r, g, b, a = px[:,:,0], px[:,:,1], px[:,:,2], px[:,:,3]
opaque = a > 0.1   # include semi-transparent anti-alias edge pixels

# ── Colour detection ──────────────────────────────────────────────────────────
# Sample some pixel values first for diagnostic
print("Corner samples (r,g,b,a):")
for label, y, x in [("top-left",5,5),("center",H//2,W//2),("mid-right",H//2,W-10)]:
    print(f"  {label}: {r[y,x]:.2f},{g[y,x]:.2f},{b[y,x]:.2f},{a[y,x]:.2f}")

# Blue: cobalt/royal blue (high B, low R)
blue = opaque & (b > 0.40) & (b > r + 0.10) & (r < 0.55)

# Red: bright red banner (high R, low G and B)
red  = opaque & (r > 0.55) & (r > g + 0.30) & (r > b + 0.30) & ~blue

# Yellow (for reference only — these pixels become transparent holes)
yellow = opaque & (r > 0.60) & (g > 0.45) & (b < 0.30) & ~blue & ~red

print(f"blue={blue.sum():,}  red={red.sum():,}  yellow={yellow.sum():,}")

if blue.sum() == 0 or red.sum() == 0:
    # Diagnostic: print actual channel ranges to tune thresholds
    print("\n--- Pixel channel ranges for opaque pixels ---")
    op_r = r[opaque]; op_g = g[opaque]; op_b = b[opaque]
    print(f"R: min={op_r.min():.2f} max={op_r.max():.2f} mean={op_r.mean():.2f}")
    print(f"G: min={op_g.min():.2f} max={op_g.max():.2f} mean={op_g.mean():.2f}")
    print(f"B: min={op_b.min():.2f} max={op_b.max():.2f} mean={op_b.mean():.2f}")

# ── SVG helpers ───────────────────────────────────────────────────────────────
# Both SVGs share the same viewBox so they overlay perfectly in Bambu Studio.
W_IN = f"{W / 96:.4f}in"
H_IN = f"{H / 96:.4f}in"
VIEWBOX = f"0 0 {W} {H}"

SVG_HEADER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    f'     width="{W_IN}" height="{H_IN}" viewBox="{VIEWBOX}">\n'
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
                paths.append(f"M {rs},{row} L {col},{row} L {col},{row+1} L {rs},{row+1} Z")
    return paths

def save_svg(mask, color_hex, filename):
    paths = mask_to_paths(mask)
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
    sz = os.path.getsize(out)
    print(f"  → {out}  ({sz//1024} KB, {len(paths):,} paths)")

print("Building SVGs...")
save_svg(blue, '#1965B0', '01_TOY_Blue')    # blue outline around TOY (+ O center dot)
save_svg(red,  '#D8231C', '02_STORY_Red')   # red banner with yellow-letter holes

print(f"\nDone — 2 SVG files in:\n{OUT_DIR}")
print("Both share the same viewBox — import both into Bambu Studio and they auto-align.")
