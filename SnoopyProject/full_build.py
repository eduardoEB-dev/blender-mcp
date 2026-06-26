"""
FULL SNOOPY DINO BUILD — single script, correct order:
  1. Clear scene
  2. Build all part geometry with connector-aware positions
  3. Add D-profile pegs (male) and socket holes (female) via boolean
  4. Apply crochet bump displacement
  5. Save

Convention: 1 unit = 1mm.  Flat of D-connector faces +Y (back of figure).

Layout (Z, bottom to top):
  0–12    feet / claws           (yellow)
  10–26   legs                   (yellow)
  22–62   body / dino shell      (blue)   — top at Z=62, socket hole at top
  62–70   neck collar            (white)  — bottom peg Z=57-62, top peg Z=70-75
  69–99   head                   (white)  — bottom at Z=69, socket at Z=69-74
  Ears & nose attached near head (black)
  Spines on back of body         (yellow)
"""
import bpy, bmesh, math, numpy as np

# ============================================================
# 0.  CLEAR
# ============================================================
for o in list(bpy.data.objects):  bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):   bpy.data.meshes.remove(m, do_unlink=True)
for m in list(bpy.data.materials):bpy.data.materials.remove(m, do_unlink=True)
for t in list(bpy.data.textures): bpy.data.textures.remove(t, do_unlink=True)
for i in list(bpy.data.images):   bpy.data.images.remove(i, do_unlink=True)
print("Cleared.")

# ============================================================
# 1.  MATERIALS
# ============================================================
def mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = rgba
        b.inputs["Roughness"].default_value   = 0.85
    return m

WHITE  = mat("Snoopy_White",  (0.95,0.95,0.95,1))
BLACK  = mat("Snoopy_Black",  (0.05,0.05,0.05,1))
BLUE   = mat("Snoopy_Blue",   (0.04,0.32,0.82,1))
YELLOW = mat("Snoopy_Yellow", (0.95,0.72,0.04,1))

# ============================================================
# 2.  GEOMETRY HELPERS
# ============================================================
def uv_sphere(name, radius, loc, seg, rings, material, scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius,segments=seg,
                                          ring_count=rings,location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.sphere_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    return o

def cylinder(name, radius, depth, verts, loc, material, scale=(1,1,1)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius,depth=depth,
                                         vertices=verts,location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    return o

def bool_op(base, tool, operation='UNION'):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = base
    base.select_set(True)
    m = base.modifiers.new("bool_tmp",'BOOLEAN')
    m.operation = operation
    m.object    = tool
    m.solver    = 'FLOAT'
    bpy.ops.object.modifier_apply(modifier="bool_tmp")
    bpy.data.objects.remove(tool, do_unlink=True)

def select_active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

# ============================================================
# 3.  D-CONNECTOR HELPERS
# ============================================================
# D-profile: cylinder with flat cut on +Y side at y = FLAT_Y
PEG_R      = 4.0     # male peg radius (mm)
SOC_R      = 4.2     # female socket radius (0.2mm gap per side)
PEG_H      = 5.0     # peg height (mm)
SOC_H      = 5.2     # socket depth (extra 0.2mm for clearance)
FLAT_Y     = 2.5     # Y distance of flat from centre

def make_d_shape(name, radius, height, loc, is_socket=False):
    """Return a D-profile cylinder mesh object at loc, centred in Z."""
    flat_y = FLAT_Y * (SOC_R / PEG_R) if is_socket else FLAT_Y
    bpy.ops.mesh.primitive_cylinder_add(radius=radius,depth=height,
                                         vertices=48,location=loc)
    cyl = bpy.context.active_object; cyl.name = name
    # Cutter cube covering Y > flat_y
    cx, cy, cz = loc
    bpy.ops.mesh.primitive_cube_add(size=2, location=(cx, cy+flat_y+10, cz))
    cutter = bpy.context.active_object; cutter.name = "d_cutter_tmp"
    cutter.scale = (radius+2, 10, height/2+1)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bool_op(cyl, cutter, 'DIFFERENCE')
    return cyl

def add_peg(parent_obj, peg_loc):
    """Boolean-UNION a D-peg onto parent_obj at peg_loc."""
    peg = make_d_shape("peg_tmp", PEG_R, PEG_H, peg_loc)
    bool_op(parent_obj, peg, 'UNION')

def add_socket(parent_obj, socket_loc):
    """Boolean-DIFFERENCE a D-socket hole into parent_obj at socket_loc."""
    soc = make_d_shape("sock_tmp", SOC_R, SOC_H, socket_loc, is_socket=True)
    bool_op(parent_obj, soc, 'DIFFERENCE')

# ============================================================
# 4.  BUILD PARTS
# ============================================================

# --- Head  (white, center Z=84, radius=15 → bottom=69, top=99) ---
head = uv_sphere("Snoopy_Head",15,(0,0,84),96,48,WHITE,(1.0,0.90,1.08))

# --- Ears  (black, hanging from top-sides of head) ---
for side,sign in [("L",-1),("R",1)]:
    ear = uv_sphere(f"Snoopy_Ear_{side}",13,(sign*14.5,-1.5,82),48,24,
                    BLACK,(7/13,4.5/13,1.0))
    ear.rotation_euler[1] = math.radians(sign*5)
    select_active(ear)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)

# --- Nose  (black oval on front of head) ---
nose = uv_sphere("Snoopy_Nose",5.5,(0,-13.5,78),32,16,BLACK,(1.0,0.45,0.75))

# --- Body  (blue, center Z=42, radius=20 → bottom=22, top=62) ---
body = uv_sphere("Snoopy_Body",20,(0,0,42),96,48,BLUE,(1.05,0.88,1.0))

# --- Neck  (white collar, Z=62-70, centre Z=66, height=8) ---
neck = cylinder("Snoopy_Neck",11,8,64,(0,0,66),WHITE,(1.0,0.90,1.0))

# --- Spines  (yellow, 5 fins on back of body) ---
SPINE_D = [(58,1.55,0.55,1.20),(63,1.40,0.50,1.45),(68,1.20,0.45,1.55),
           (73,1.00,0.40,1.40),(78,0.80,0.38,1.15)]
for i,(z,sx,sy,sz) in enumerate(SPINE_D):
    uv_sphere(f"Snoopy_Spine_{i+1:02d}",6,(0,17,z),32,16,YELLOW,(sx,sy,sz))

# --- Legs + Feet  (yellow) ---
for side,sign in [("L",-1),("R",1)]:
    leg = cylinder(f"Snoopy_Leg_{side}",6.5,14,32,(sign*10,2,18),
                   YELLOW,(1.0,0.88,1.0))

    bpy.ops.mesh.primitive_uv_sphere_add(radius=7,segments=32,ring_count=16,
                                          location=(sign*10,-2,6))
    foot = bpy.context.active_object; foot.name = f"Snoopy_Foot_{side}"
    foot.scale=(1.25,1.05,0.85)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.ops.object.shade_smooth()
    foot.data.materials.append(YELLOW)

    for dx,dy,dz in [(-4,-8,5),(0,-9,4.5),(4,-8,5)]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=3.2,segments=16,ring_count=8,
                                              location=(sign*10+dx,dy,dz))
        toe = bpy.context.active_object; toe.name="toe_tmp"
        toe.scale=(0.95,1.10,0.80)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        bool_op(foot, toe, 'UNION')

    select_active(foot)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

print("Base geometry done.")

# ============================================================
# 5.  D-PROFILE CONNECTORS
# ============================================================
# Neck top peg  (Z=70 → peg centre at 70+2.5=72.5, range 70-75)
add_peg(neck, (0, 0, 72.5))
# Neck bottom peg  (Z=62 → peg centre at 62-2.5=59.5, range 57-62)
add_peg(neck, (0, 0, 59.5))

# Head socket  (opening at Z=69, depth 5mm → centre at 69+2.6=71.6, range 69-74)
add_socket(head, (0, 0, 71.5))

# Body socket  (opening at Z=62, depth 5mm going DOWN → centre at 62-2.6=59.4)
add_socket(body, (0, 0, 59.5))

print("Connectors done.")

# Rebuild UVs for neck (booleans mess up UVs)
select_active(neck)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode='OBJECT')

# ============================================================
# 6.  CROCHET TEXTURE
# ============================================================
SIZE          = 512
BUMPS_PER_ROW = 16
STITCH_MM     = 3.0
DISP_STR      = 1.5

print("Generating crochet bump map...")
CELL_W = SIZE / BUMPS_PER_ROW
CELL_H = CELL_W * 0.80
y_g, x_g = np.mgrid[0:SIZE,0:SIZE].astype(np.float32)
arr = np.zeros((SIZE,SIZE),dtype=np.float32)
for row in range(-1, int(SIZE/CELL_H)+3):
    for col in range(-1, int(SIZE/CELL_W)+3):
        cx=(col+0.5+(row%2)*0.5)*CELL_W; cy=(row+0.5)*CELL_H
        nx=(x_g-cx)/(CELL_W*0.46);       ny=(y_g-cy)/(CELL_H*0.46)
        r2=nx*nx+ny*ny
        arr=np.maximum(arr,np.where(r2<1,(1-r2)**1.6,0).astype(np.float32))

img = bpy.data.images.new("CrochetBumps",SIZE,SIZE,alpha=False,float_buffer=True)
f   = np.flipud(arr)
img.pixels[:] = np.stack([f,f,f,np.ones_like(f)],axis=-1).ravel().tolist()
img.pack()

tex = bpy.data.textures.new("CrochetTex",'IMAGE')
tex.image=img; tex.extension='REPEAT'

def calc_uv(obj):
    return math.pi*max(obj.dimensions) / (STITCH_MM*BUMPS_PER_ROW)

def scale_uvs(obj, s):
    bm=bmesh.new(); bm.from_mesh(obj.data)
    uv=bm.loops.layers.uv.active
    if uv:
        for f in bm.faces:
            for l in f.loops:
                l[uv].uv.x=(l[uv].uv.x-0.5)*s+0.5
                l[uv].uv.y=(l[uv].uv.y-0.5)*s+0.5
    bm.to_mesh(obj.data); obj.data.update(); bm.free()

# (name, subdivision_level)
PARTS=[("Snoopy_Head",1),("Snoopy_Ear_L",1),("Snoopy_Ear_R",1),
       ("Snoopy_Nose",0),("Snoopy_Body",1),("Snoopy_Neck",1),
       ("Snoopy_Leg_L",1),("Snoopy_Leg_R",1),
       ("Snoopy_Foot_L",1),("Snoopy_Foot_R",1),
       ("Snoopy_Spine_01",1),("Snoopy_Spine_02",1),("Snoopy_Spine_03",1),
       ("Snoopy_Spine_04",1),("Snoopy_Spine_05",1)]

for name,subd in PARTS:
    obj=bpy.data.objects.get(name)
    if not obj: print(f"  SKIP: {name}"); continue
    select_active(obj)
    scale_uvs(obj, calc_uv(obj))
    if subd:
        m=obj.modifiers.new("SubdTmp","SUBSURF")
        m.levels=subd; m.subdivision_type='CATMULL_CLARK'
        bpy.ops.object.modifier_apply(modifier="SubdTmp")
    m=obj.modifiers.new("Crochet","DISPLACE")
    m.texture=tex; m.strength=DISP_STR; m.mid_level=0.5
    m.texture_coords='UV'; m.direction='NORMAL'
    bpy.ops.object.modifier_apply(modifier="Crochet")
    print(f"  {name}: {len(obj.data.vertices):,} verts")

# ============================================================
# 7.  SAVE
# ============================================================
bpy.ops.wm.save_mainfile()
print("\n=== BUILD COMPLETE ===")
for o in sorted(bpy.data.objects,key=lambda x:x.name):
    print(f"  {o.name}: {[round(d,1) for d in o.dimensions]}")
