import bpy, os, math

PNG_SRC = r"d:\Blender\blender-mcp\CupProjects\Images\Toy_Story_Layers\BuzzChestPlate.png"
OUT_DIR  = r"d:\Blender\blender-mcp\CupProjects\Images\Toy_Story_Layers\Buzz_SVGs"

# Get PNG dimensions
img = bpy.data.images.load(PNG_SRC)
W, H = img.size
bpy.data.images.remove(img)
print(f"Canvas: {W}×{H}")

# ── Parallelogram (same constants as gen_buzz_svgs.py) ────────────────────────
LY_LX, LY_RX  = 0.620*W, 0.860*W
LY_TY, LY_BY  = 0.160*H, 0.340*H
LY_SKEW        = 0.025*W
LY_TL = (LY_LX+LY_SKEW, LY_TY)
LY_TR = (LY_RX+LY_SKEW, LY_TY)
LY_BR = (LY_RX,          LY_BY)
LY_BL = (LY_LX,          LY_BY)

BADGE_CX = (LY_TL[0] + LY_TR[0] + LY_BR[0] + LY_BL[0]) / 4
BADGE_CY = (LY_TY + LY_BY) / 2
BADGE_W  = LY_RX - LY_LX
BADGE_H  = LY_BY - LY_TY

def poly_path(pts):
    return "M " + " L ".join(f"{p[0]:.2f},{p[1]:.2f}" for p in pts) + " Z"

# ── Build LIGHTYEAR text curve ────────────────────────────────────────────────
for o in list(bpy.data.objects):
    if o.type in ('FONT', 'CURVE') and o.name.startswith("Text"):
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.text_add(location=(0, 0, 0))
txt = bpy.context.active_object
txt.data.body    = "LIGHTYEAR"
txt.data.align_x = 'CENTER'
txt.data.align_y = 'CENTER'
txt.data.size    = 1.0

for font_path in [r"C:\Windows\Fonts\impact.ttf",
                  r"C:\Windows\Fonts\ariblk.ttf",
                  r"C:\Windows\Fonts\arialbd.ttf"]:
    if os.path.exists(font_path):
        txt.data.font = bpy.data.fonts.load(font_path)
        print(f"Font: {os.path.basename(font_path)}")
        break
else:
    print("Font: Blender default")

bpy.context.view_layer.objects.active = txt
txt.select_set(True)
bpy.ops.object.convert(target='CURVE')
crv = bpy.context.active_object

# ── Compute text bounding box ─────────────────────────────────────────────────
xs, ys = [], []
for spline in crv.data.splines:
    if spline.type == 'BEZIER':
        for pt in spline.bezier_points:
            xs += [pt.co.x, pt.handle_left.x, pt.handle_right.x]
            ys += [pt.co.y, pt.handle_left.y, pt.handle_right.y]
    else:
        for pt in spline.points:
            xs.append(pt.co.x); ys.append(pt.co.y)

if not xs:
    print("ERROR: no curve data"); raise SystemExit(1)

text_cx = (min(xs) + max(xs)) / 2
text_cy = (min(ys) + max(ys)) / 2
text_w  = max(xs) - min(xs)
text_h  = max(ys) - min(ys)
print(f"Text local bounds: {text_w:.3f} × {text_h:.3f}")

PAD   = 0.10
scale = min((BADGE_W * (1-2*PAD)) / text_w,
            (BADGE_H * (1-2*PAD)) / text_h)
print(f"Scale: {scale:.4f}")

# ── Coordinate transforms — skew baked into tx() ─────────────────────────────
# The parallelogram's italic angle: top edge is offset +LY_SKEW to the right.
# skewX(-angle) around badge centre in SVG space:
#   new_svg_x = svg_x - (svg_y - BADGE_CY) * tan(angle)
# After substituting svg_x and svg_y in terms of Blender coords:
#   tx(bl_x, bl_y) = (bl_x - text_cx)*scale + BADGE_CX
#                    + (bl_y - text_cy)*scale * skew_tan
# (The +skew_tan term comes from -(−(bl_y−text_cy)*scale) * skew_tan.)
skew_deg = math.degrees(math.atan(LY_SKEW / BADGE_H))
skew_tan = math.tan(math.radians(skew_deg))
print(f"Italic skewX baked in: -{skew_deg:.1f}°")

def tx(bl_x, bl_y):
    return ((bl_x - text_cx) * scale + BADGE_CX
            + (bl_y - text_cy) * scale * skew_tan)

def ty(bl_y):
    return -(bl_y - text_cy) * scale + BADGE_CY

# ── Extract bezier/poly paths with skew baked into coordinates ────────────────
paths = []
for spline in crv.data.splines:
    if spline.type == 'BEZIER':
        pts = spline.bezier_points
        if not pts: continue
        p0 = pts[0]
        d  = f"M {tx(p0.co.x,p0.co.y):.3f},{ty(p0.co.y):.3f}"
        for i in range(1, len(pts)):
            pr, cu = pts[i-1], pts[i]
            d += (f" C {tx(pr.handle_right.x,pr.handle_right.y):.3f},"
                  f"{ty(pr.handle_right.y):.3f}"
                  f" {tx(cu.handle_left.x,cu.handle_left.y):.3f},"
                  f"{ty(cu.handle_left.y):.3f}"
                  f" {tx(cu.co.x,cu.co.y):.3f},{ty(cu.co.y):.3f}")
        if spline.use_cyclic_u:
            pr, cu = pts[-1], pts[0]
            d += (f" C {tx(pr.handle_right.x,pr.handle_right.y):.3f},"
                  f"{ty(pr.handle_right.y):.3f}"
                  f" {tx(cu.handle_left.x,cu.handle_left.y):.3f},"
                  f"{ty(cu.handle_left.y):.3f}"
                  f" {tx(cu.co.x,cu.co.y):.3f},{ty(cu.co.y):.3f}")
    else:
        pts_list = spline.points
        if not pts_list: continue
        d = f"M {tx(pts_list[0].co.x,pts_list[0].co.y):.3f},{ty(pts_list[0].co.y):.3f}"
        for pt in pts_list[1:]:
            d += f" L {tx(pt.co.x,pt.co.y):.3f},{ty(pt.co.y):.3f}"
    d += " Z"   # always close letter contours
    paths.append(d)

text_path_d = " ".join(paths)
print(f"Generated {len(paths)} sub-paths")

# ── Write SVG (no <g transform> — skew is in the coordinates) ────────────────
ly_outline = poly_path([LY_TL, LY_TR, LY_BR, LY_BL])
stroke_w   = max(4.0, H * 0.018)

svg = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    f'     width="{W}px" height="{H}px" viewBox="0 0 {W} {H}">\n'
    f'  <path fill="none" stroke="#000000" stroke-width="{stroke_w:.1f}"\n'
    f'        stroke-linejoin="miter" d="{ly_outline}"/>\n'
    f'  <path fill="#000000" fill-rule="evenodd" d="{text_path_d}"/>\n'
    '</svg>\n'
)

out = os.path.join(OUT_DIR, '05_Lightyear_Black.svg')
with open(out, 'w', encoding='utf-8') as f:
    f.write(svg)
print(f"Written: {out}")

bpy.data.objects.remove(crv, do_unlink=True)
print("Done.")
