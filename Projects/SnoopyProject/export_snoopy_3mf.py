"""
Export each Snoopy part as its own 3MF file.
Output: D:/Blender/Export/Snoopy/<name>.3mf
Unit: millimeter (1 Blender unit = 1mm convention).

NOTE: Print brims (5mm width, 0.2mm gap) are slicer settings, not model geometry.
Set them in Bambu Studio / PrusaSlicer per-part after importing these files.
"""
import bpy, bmesh, zipfile, os
from mathutils import Vector

OUT_DIR = r"D:\Blender\Export\Snoopy"
os.makedirs(OUT_DIR, exist_ok=True)

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
                Target="/3D/3dmodel.model" Id="rel0"/>
</Relationships>'''

def obj_to_verts_tris(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    mw = obj.matrix_world
    verts = [mw @ v.co for v in bm.verts]
    tris  = [(f.verts[0].index, f.verts[1].index, f.verts[2].index) for f in bm.faces]
    bm.free()
    return verts, tris

def build_3mf_xml(obj_name, verts, tris):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
        '  <resources>',
        f'    <object id="1" name="{obj_name}" type="model">',
        '      <mesh>',
        '        <vertices>',
    ]
    for v in verts:
        lines.append(f'          <vertex x="{v.x:.5f}" y="{v.y:.5f}" z="{v.z:.5f}"/>')
    lines += ['        </vertices>', '        <triangles>']
    for t in tris:
        lines.append(f'          <triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>')
    lines += ['        </triangles>','      </mesh>','    </object>',
              '  </resources>',
              '  <build>','    <item objectid="1"/>','  </build>','</model>']
    return '\n'.join(lines)

def export_obj(obj):
    path = os.path.join(OUT_DIR, f"{obj.name}.3mf")
    print(f"  {obj.name}...", end='')
    verts, tris = obj_to_verts_tris(obj)
    xml = build_3mf_xml(obj.name, verts, tris)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', CONTENT_TYPES)
        zf.writestr('_rels/.rels', RELS)
        zf.writestr('3D/3dmodel.model', xml)
    kb = os.path.getsize(path)//1024
    print(f" {len(verts):,} verts, {len(tris):,} tris → {kb} KB")
    return path

# Parts to export (all Snoopy_ objects)
parts = sorted([o for o in bpy.data.objects if o.name.startswith("Snoopy_")],
               key=lambda o: o.name)

print(f"\nExporting {len(parts)} parts to {OUT_DIR}")
print(f"{'─'*50}")
exported = []
for obj in parts:
    if obj.type != 'MESH':
        print(f"  SKIP (not mesh): {obj.name}")
        continue
    p = export_obj(obj)
    exported.append(p)

print(f"\n{'─'*50}")
print(f"Done: {len(exported)} files exported.")
print(f"\nSlicer setup (per part):")
print(f"  Brim: Outer, width=5mm, gap=0.2mm")
print(f"  Colors: White=Head/Neck/Ears-Nose, Blue=Body/Spines, Yellow=Legs/Feet")
print(f"  Note: Black parts = Ear_L, Ear_R, Nose")
