import bpy, os

PNG_SRC = r"d:\Blender\blender-mcp\CupProjects\Images\Toy_Story_Layers\BuzzChestPlate.png"
OUT_DIR  = r"d:\Blender\blender-mcp\CupProjects\Images\Toy_Story_Layers\Buzz_SVGs"
os.makedirs(OUT_DIR, exist_ok=True)

# Detect source PNG dimensions
img = bpy.data.images.load(PNG_SRC)
W, H = img.size
bpy.data.images.remove(img)
print(f"Source PNG: {W}×{H}")

# ── Design proportions (all as fractions of W × H) ───────────────────────────
# Based on visual analysis of BuzzChestPlate.png + BuzzCupExample.png.
# Tweak these constants to nudge positions/sizes.

# 3 identical oval button holes (left cluster)
OVAL_RX = 0.030 * W   # half-width  (slimmer)
OVAL_RY = 0.130 * H   # half-height (taller than wide → vertical orientation)

# Each oval steps progressively lower (diagonal top-left → bottom-right)
OVAL_CENTERS = [
    (0.175 * W, 0.450 * H),  # button 1  (blue  — leftmost,  highest)
    (0.258 * W, 0.540 * H),  # button 2  (green — centre,    middle)
    (0.340 * W, 0.630 * H),  # button 3  (red   — rightmost, lowest)
]

# Large circular hole (right side, red button)
CIR_CX = 0.755 * W
CIR_CY = 0.560 * H
CIR_R  = 0.105 * H   # circle radius (matches height of ovals roughly)

# LIGHTYEAR badge parallelogram (upper right of green panel)
# top edge is shifted rightward by SKEW → makes it look slanted
LY_LX   = 0.620 * W   # left  x at bottom
LY_RX   = 0.860 * W   # right x at bottom
LY_TY   = 0.160 * H   # top   y
LY_BY   = 0.340 * H   # bottom y
LY_SKEW = 0.025 * W   # how much the top edge is shifted right vs bottom

# Parallelogram corner points (TL TR BR BL)
LY_TL = (LY_LX + LY_SKEW, LY_TY)
LY_TR = (LY_RX + LY_SKEW, LY_TY)
LY_BR = (LY_RX,             LY_BY)
LY_BL = (LY_LX,             LY_BY)

# ── SVG geometry helpers ──────────────────────────────────────────────────────

def ellipse_path(cx, cy, rx, ry):
    """Clockwise ellipse path via cubic bezier (for even-odd holes)."""
    k = 0.5523
    return (
        f"M {cx-rx:.2f},{cy:.2f} "
        f"C {cx-rx:.2f},{cy-ry*k:.2f} {cx-rx*k:.2f},{cy-ry:.2f} {cx:.2f},{cy-ry:.2f} "
        f"C {cx+rx*k:.2f},{cy-ry:.2f} {cx+rx:.2f},{cy-ry*k:.2f} {cx+rx:.2f},{cy:.2f} "
        f"C {cx+rx:.2f},{cy+ry*k:.2f} {cx+rx*k:.2f},{cy+ry:.2f} {cx:.2f},{cy+ry:.2f} "
        f"C {cx-rx*k:.2f},{cy+ry:.2f} {cx-rx:.2f},{cy+ry*k:.2f} {cx-rx:.2f},{cy:.2f} Z"
    )

def circle_path(cx, cy, r):
    return ellipse_path(cx, cy, r, r)

def rect_path(x, y, w, h):
    return f"M {x:.2f},{y:.2f} L {x+w:.2f},{y:.2f} L {x+w:.2f},{y+h:.2f} L {x:.2f},{y+h:.2f} Z"

def poly_path(pts):
    d = f"M {pts[0][0]:.2f},{pts[0][1]:.2f}"
    for p in pts[1:]:
        d += f" L {p[0]:.2f},{p[1]:.2f}"
    return d + " Z"

# ── SVG file writer (full-image viewBox) ──────────────────────────────────────
FULL_HDR = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    f'     width="{W}px" height="{H}px" viewBox="0 0 {W} {H}">\n'
)

def save_full(body, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(FULL_HDR + body + '</svg>\n')
    print(f"  → {path}")

# ── 01  Green rectangle with holes ───────────────────────────────────────────
outer   = rect_path(0, 0, W, H)
holes   = " ".join(ellipse_path(cx, cy, OVAL_RX, OVAL_RY) for cx, cy in OVAL_CENTERS)
holes  += " " + circle_path(CIR_CX, CIR_CY, CIR_R)
holes  += " " + poly_path([LY_TL, LY_TR, LY_BR, LY_BL])

save_full(
    f'  <path fill="#2DB831" fill-rule="evenodd"\n'
    f'        d="{outer} {holes}"/>\n',
    '01_Green_Rectangle.svg'
)

# ── 02  Reusable oval (its own small viewBox) ─────────────────────────────────
# Size exactly matches the holes in the green rectangle.
# User imports this 3 times, assigns blue / green / red in Bambu Studio.
OW = OVAL_RX * 2
OH = OVAL_RY * 2
oval_svg = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    f'     width="{OW:.2f}px" height="{OH:.2f}px" viewBox="0 0 {OW:.2f} {OH:.2f}">\n'
    f'  <path fill="#808080" d="{ellipse_path(OVAL_RX, OVAL_RY, OVAL_RX, OVAL_RY)}"/>\n'
    '</svg>\n'
)
path = os.path.join(OUT_DIR, '02_Oval.svg')
open(path, 'w').write(oval_svg)
print(f"  → {path}  ({OW:.1f}×{OH:.1f} px — import 3× and recolor)")

# ── 03  Circle (for the red button) ──────────────────────────────────────────
# Sized to EXACTLY fill the circular hole in the green rectangle.
CD = CIR_R * 2
circle_svg = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    f'     width="{CD:.2f}px" height="{CD:.2f}px" viewBox="0 0 {CD:.2f} {CD:.2f}">\n'
    f'  <path fill="#D8231C" d="{circle_path(CIR_R, CIR_R, CIR_R)}"/>\n'
    '</svg>\n'
)
path = os.path.join(OUT_DIR, '03_Circle.svg')
open(path, 'w').write(circle_svg)
print(f"  → {path}  ({CD:.1f}×{CD:.1f} px — color red in Bambu Studio)")

# ── 04  LIGHTYEAR badge — yellow parallelogram ────────────────────────────────
ly_d = poly_path([LY_TL, LY_TR, LY_BR, LY_BL])
save_full(
    f'  <path fill="#F5C518" d="{ly_d}"/>\n',
    '04_Lightyear_Yellow.svg'
)

# ── 05  LIGHTYEAR badge — black outline + text ────────────────────────────────
# Black stroke outline + "LIGHTYEAR" text centred inside the parallelogram.
ly_cx    = ((LY_TL[0] + LY_TR[0]) / 2 + (LY_BL[0] + LY_BR[0]) / 2) / 2
ly_cy    = (LY_TY + LY_BY) / 2
font_h   = (LY_BY - LY_TY) * 0.46   # font size = ~46% of badge height
stroke_w = max(1.5, H * 0.007)

save_full(
    f'  <!-- Black parallelogram outline -->\n'
    f'  <path fill="none" stroke="#000000" stroke-width="{stroke_w:.1f}"\n'
    f'        stroke-linejoin="miter" d="{ly_d}"/>\n'
    f'  <!-- LIGHTYEAR text centred in badge -->\n'
    f'  <text x="{ly_cx:.2f}" y="{ly_cy + font_h * 0.36:.2f}"\n'
    f'        text-anchor="middle"\n'
    f'        font-family="Arial Black,Impact,Franklin Gothic Heavy,sans-serif"\n'
    f'        font-size="{font_h:.2f}" font-weight="900" letter-spacing="1.5"\n'
    f'        fill="#000000">LIGHTYEAR</text>\n',
    '05_Lightyear_Black.svg'
)

print(f"\nAll 5 SVG files written to:\n{OUT_DIR}")
print("""
Overlay order in Bambu Studio (bottom → top):
  01_Green_Rectangle  — green base with all holes
  02_Oval ×3          — place one over each oval hole; assign blue / green / red
  03_Circle           — place over the round hole; assign red
  04_Lightyear_Yellow — auto-aligns (same viewBox as green rect)
  05_Lightyear_Black  — auto-aligns on top of yellow
""")
