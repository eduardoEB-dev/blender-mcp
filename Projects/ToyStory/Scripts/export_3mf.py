import bpy, bmesh, zipfile, os
from mathutils import Matrix

OUTPUT = r"d:\Blender\Export\SnoopyCupProj.3mf"

# ---- helpers ----
def triangulated_world_verts_tris(obj):
    """Return (verts_list, tris_list) in world space, fully triangulated."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    mw = obj.matrix_world
    verts = [(mw @ v.co) for v in bm.verts]
    tris  = [(f.verts[0].index, f.verts[1].index, f.verts[2].index) for f in bm.faces]
    bm.free()
    return verts, tris

def object_xml(obj_id, name, verts, tris):
    lines = [f'    <object id="{obj_id}" name="{name}" type="model">',
             '      <mesh>',
             '        <vertices>']
    for v in verts:
        lines.append(f'          <vertex x="{v.x:.6f}" y="{v.y:.6f}" z="{v.z:.6f}"/>')
    lines.append('        </vertices>')
    lines.append('        <triangles>')
    for t in tris:
        lines.append(f'          <triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>')
    lines.append('        </triangles>')
    lines.append('      </mesh>')
    lines.append('    </object>')
    return '\n'.join(lines)

# ---- collect objects ----
names = ['EFCooler_Cup', 'Snoopy_Black', 'Snoopy_White', 'Woodstock_Yellow']
objects = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
print(f"Exporting {len(objects)} objects: {[o.name for o in objects]}")

# ---- build 3MF XML ----
resources = []
build_items = []
for i, obj in enumerate(objects, start=1):
    print(f"  Triangulating {obj.name}...")
    verts, tris = triangulated_world_verts_tris(obj)
    print(f"    {len(verts)} verts, {len(tris)} tris")
    resources.append(object_xml(i, obj.name, verts, tris))
    build_items.append(f'    <item objectid="{i}"/>')

model_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
{chr(10).join(resources)}
  </resources>
  <build>
{chr(10).join(build_items)}
  </build>
</model>'''

content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>'''

rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model" Id="rel0"/>
</Relationships>'''

# ---- write ZIP ----
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('[Content_Types].xml', content_types)
    zf.writestr('_rels/.rels', rels)
    zf.writestr('3D/3dmodel.model', model_xml)

size_kb = os.path.getsize(OUTPUT) // 1024
print(f"\nExported: {OUTPUT}  ({size_kb} KB)")
print("Import this file into Bambu Studio → assign filaments to each part.")
