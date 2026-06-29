import bpy, numpy as np, os
from collections import deque

PNG_SRC = r"d:\Blender\Images\SnoopyWSCloudsPNG.png"
OUT_DIR  = r"d:\Blender\Images\Layers"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- load full-res image ----------
orig = bpy.data.images.load(PNG_SRC)
W, H = orig.size   # 1494 x 1053
px   = np.array(orig.pixels[:], dtype=np.float32).reshape(H, W, 4)
px   = px[::-1].copy()   # flip to top-down
bpy.data.images.remove(orig)
print(f"Loaded {W}x{H}")

r,g,b,a = px[:,:,0], px[:,:,1], px[:,:,2], px[:,:,3]
opaque  = a > 0.4

# ---------- color separation ----------
black  = (r < 0.35) & (g < 0.35) & (b < 0.35) & opaque
# Broader yellow: catches Woodstock's shaded/feathered areas too
yellow = (r > 0.45) & (g > 0.25) & (b < 0.45) & (r > b + 0.15) & opaque & ~black
wc     = ~black & ~yellow & opaque

bg = np.zeros((H, W), bool)
q  = deque()
def seed(y, x):
    if wc[y,x] and not bg[y,x]: bg[y,x]=True; q.append((y,x))
for x in range(W): seed(0,x); seed(H-1,x)
for y in range(H): seed(y,0); seed(y,W-1)
for y,x in zip(*np.where(~opaque)):
    for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
        ny,nx=y+dy,x+dx
        if 0<=ny<H and 0<=nx<W and wc[ny,nx] and not bg[ny,nx]:
            bg[ny,nx]=True; q.append((ny,nx))
while q:
    y,x=q.popleft()
    for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
        ny,nx=y+dy,x+dx
        if 0<=ny<H and 0<=nx<W and wc[ny,nx] and not bg[ny,nx]:
            bg[ny,nx]=True; q.append((ny,nx))
white = wc & ~bg

def dilate(m, n=2):
    for _ in range(n):
        m2=m.copy()
        m2[:-1]|=m[1:]; m2[1:]|=m[:-1]
        m2[:,:-1]|=m[:,1:]; m2[:,1:]|=m[:,:-1]
        m=m2
    return m

white  = dilate(white, 2) & ~black
yellow = dilate(yellow, 5) & ~black   # more dilation fills Woodstock's feather gaps

# Remove small isolated white regions (artifacts like the line above the cloud)
def remove_small_components(mask, min_size=1500):
    h, w = mask.shape
    visited = np.zeros((h, w), bool)
    result = mask.copy()
    ys, xs = np.where(mask)
    for sy, sx in zip(ys.tolist(), xs.tolist()):
        if visited[sy, sx]:
            continue
        component = []
        q = deque([(sy, sx)])
        visited[sy, sx] = True
        while q:
            y, x = q.popleft()
            component.append((y, x))
            for dy, dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny, nx = y+dy, x+dx
                if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not visited[ny,nx]:
                    visited[ny,nx] = True
                    q.append((ny, nx))
        if len(component) < min_size:
            for cy, cx in component:
                result[cy, cx] = False
    return result

print("Filtering small white artifacts...")
white = remove_small_components(white, min_size=1500)

print(f"black={black.sum():,}  yellow={yellow.sum():,}  white={white.sum():,}")

# ---------- mask → SVG path strings ----------
# Each row: find runs of "on" pixels → one closed rect path per run
# viewBox is 0 0 1494 1053, mask is also 1494x1053 → 1 px = 1 SVG unit

def mask_to_paths(mask):
    h, w = mask.shape
    paths = []
    for row in range(h):
        in_run = False
        rs = 0
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

# ---------- write SVG ----------
SVG_HEADER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    '     width="20.75in" height="14.625in" viewBox="0 0 1494 1053">\n'
)

def save_svg(mask, color_hex, filename):
    print(f"Building paths for {filename}...")
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
    print(f"  → {out}  ({os.path.getsize(out)//1024} KB, {len(paths):,} paths)")

save_svg(black,  '#000000', '01_Black_Outline')
save_svg(yellow, '#FFB900', '02_Yellow_Woodstock')
save_svg(white,  '#FFFFFF', '03_White_Fill')

print(f"\nDone — 3 SVG files with real path data in:\n{OUT_DIR}")
