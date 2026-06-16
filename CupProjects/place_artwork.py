import bpy, bmesh, numpy as np, os
from collections import deque

CUP_NAME   = "EFCooler_Cup"
IMAGE_PATH = r"d:\Blender\Images\SnoopyWSCloudsPNG.png"
OUT_BLEND  = r"d:\Blender\SnoopyCupProj.blend"
OUT_DIR    = r"d:\Blender\Export"

ART_X_MIN, ART_X_MAX =  3.0, 87.0   # 84mm wide, nearly full cup width
ART_Z_MIN, ART_Z_MAX = 54.0, 113.0  # 59mm tall  →  84/59 = 1.42 matches image ratio
Y_FRONT  = -100.0  # in front of the front face (cup min-Y = -87.88)
THICK_MM = 1.2
IMG_W, IMG_H = 300, 211  # 300/211 = 1.42 — matches original 1494x1053 exactly

# ---------- image ----------
def load_pixels(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px[::-1].copy()

def resize(arr, th, tw):
    h, w = arr.shape[:2]
    ri = np.round(np.linspace(0, h-1, th)).astype(int)
    ci = np.round(np.linspace(0, w-1, tw)).astype(int)
    return arr[np.ix_(ri, ci)]

def dilate(m, n=1):
    for _ in range(n):
        m2 = m.copy()
        m2[:-1] |= m[1:]; m2[1:] |= m[:-1]
        m2[:,:-1] |= m[:,1:]; m2[:,1:] |= m[:,:-1]
        m = m2
    return m

def get_masks(pixels, tw, th):
    s = resize(pixels, th, tw)
    r,g,b,a = s[:,:,0],s[:,:,1],s[:,:,2],s[:,:,3]
    op     = a > 0.4
    black  = (r<0.35)&(g<0.35)&(b<0.35)&op
    yellow = (r>0.60)&(g>0.40)&(b<0.35)&op
    wc     = ~black&~yellow&op

    h,w = th,tw
    bg = np.zeros((h,w),bool); q=deque()
    def seed(y,x):
        if wc[y,x] and not bg[y,x]: bg[y,x]=True; q.append((y,x))
    for x in range(w): seed(0,x); seed(h-1,x)
    for y in range(h): seed(y,0); seed(y,w-1)
    for y,x in zip(*np.where(~op)):
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<h and 0<=nx<w and wc[ny,nx] and not bg[ny,nx]:
                bg[ny,nx]=True; q.append((ny,nx))
    while q:
        y,x=q.popleft()
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<h and 0<=nx<w and wc[ny,nx] and not bg[ny,nx]:
                bg[ny,nx]=True; q.append((ny,nx))
    white = wc&~bg
    white  = dilate(white,1)&~black
    yellow = dilate(yellow,1)&~black
    print(f"black={black.sum()} yellow={yellow.sum()} white={white.sum()}")
    return black, yellow, white

# ---------- mesh ----------
def mask_to_obj(mask, name, x0,x1,z0,z1,yf):
    if not mask.any(): print(f"skip {name}"); return None
    h,w = mask.shape
    xs = np.linspace(x0,x1,w+1); zs = np.linspace(z1,z0,h+1)
    gx,gz = np.meshgrid(xs,zs)
    gy = np.full_like(gx,yf)
    verts = np.stack([gx.ravel(),gy.ravel(),gz.ravel()],axis=1).tolist()
    ro,co = np.where(mask); s=w+1
    faces = list(zip((ro*s+co).tolist(),(ro*s+co+1).tolist(),
                     ((ro+1)*s+co+1).tolist(),((ro+1)*s+co).tolist()))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts,[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me)
    # Drop isolated verts
    dead=[v for v in bm.verts if not v.link_faces]
    if dead: bmesh.ops.delete(bm,geom=dead,context='VERTS')
    # Dissolve interior (non-boundary) edges → one clean polygon per connected region
    interior=[e for e in bm.edges if not e.is_boundary]
    if interior:
        bmesh.ops.dissolve_edges(bm,edges=interior,use_verts=True,use_face_split=False)
    bm.to_mesh(me); bm.free()
    obj=bpy.data.objects.new(name,me)
    bpy.context.collection.objects.link(obj)
    print(f"{name}: {len(faces)} pixel faces → dissolved"); return obj

def bake(obj):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me_new = bpy.data.meshes.new_from_object(ev)
    me_old = obj.data
    obj.modifiers.clear()
    obj.data = me_new
    bpy.data.meshes.remove(me_old)

def set_mat(obj,name,rgba):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=rgba; obj.data.materials.clear(); obj.data.materials.append(m)

# ---------- main ----------
print("=== Snoopy Artwork ===")

# Remove any previous artwork objects
for name in ['Snoopy_Black', 'Woodstock_Yellow', 'Snoopy_White']:
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        print(f"Removed old {name}")

cup = bpy.data.objects[CUP_NAME]
px  = load_pixels(IMAGE_PATH)
print(f"image {px.shape[1]}x{px.shape[0]}")

bk,yw,wh = get_masks(px, IMG_W, IMG_H)
a = (ART_X_MIN,ART_X_MAX,ART_Z_MIN,ART_Z_MAX,Y_FRONT)
ob = mask_to_obj(bk,"Snoopy_Black",*a)
oy = mask_to_obj(yw,"Woodstock_Yellow",*a)
ow = mask_to_obj(wh,"Snoopy_White",*a)

set_mat(ob,"Mat_Black",(0,0,0,1))
set_mat(oy,"Mat_Yellow",(1.0,0.75,0,1))
set_mat(ow,"Mat_White",(1,1,1,1))

for obj in (ob,oy,ow):
    if obj is None: continue
    sw=obj.modifiers.new("SW","SHRINKWRAP")
    sw.target=cup; sw.wrap_mode='ON_SURFACE'; sw.offset=0.0
    sol=obj.modifiers.new("SOL","SOLIDIFY")
    sol.thickness=THICK_MM; sol.offset=-1.0; sol.use_even_offset=True

print("baking modifiers...")
for obj in (ob,oy,ow):
    if obj is None: continue
    bake(obj); print(f"  {obj.name} done")

print("recalculating normals...")
for obj in (ob,oy,ow):
    if obj is None: continue
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT'); obj.select_set(False)

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("blend saved")

os.makedirs(OUT_DIR, exist_ok=True)
for obj in [cup,ob,oy,ow]:
    if obj is None: continue
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active=obj
    path=os.path.join(OUT_DIR,f"{obj.name}.stl")
    bpy.ops.wm.stl_export(filepath=path,export_selected_objects=True)
    print(f"exported {path}")

print("=== done ===")
