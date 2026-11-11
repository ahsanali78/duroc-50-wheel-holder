#!/usr/bin/env python3
"""
Parametric CAD generator for the 29+ (SUNringle Duroc 50 + 29x3.0") Dual Bicycle Wheel Holder.

Adapted from Trykpaa's MakerWorld "Bicycle wheel holder" (ID 1600179) to fit:
  - Rims: SUNringle Duroc 50 (50.0 mm outer width, 46.0 mm inner width, 16.5 mm height)
  - Tires: 29 x 3.0" (e.g. Bontrager XR2 Team Issue, ~76-78 mm mounted width)
  - Hubs: Boost 110x15 front / Boost 148x12 rear
  - Printer bed: 256 x 256 mm (Bambu Lab X1 / P1 / A1), printed flat on its side (Z_plate = 0..36 mm)

Usage:
  uv run --with build123d python3 generate_wheel_holder_29plus.py
"""

from __future__ import annotations

import math
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile

import build123d as bd

# ============================================================================
# Key Parametric Dimensions (all units in mm)
# Coordinate convention matches original STEP:
#   Z = 0         : Vertical wall mounting plane (-Z extends outward from wall)
#   Y = 0         : Top edge of wall mounting backplate (-Y goes downward)
#   X = -18..+18  : 36.0 mm bracket width (passes between spokes; Z-height on plate)
# ============================================================================

HALF_WIDTH_X = 18.0       # 36.0 mm total width
CHAMFER_X = 1.0           # 1.0 mm 45-deg perimeter chamfer on exposed X = +-18 edges

# Rim pocket dimensions (50.0 mm Duroc 50 rim + 3.0 mm clearance per side = 56.0 mm)
SLOT_WIDTH = 56.0
HALF_SLOT = SLOT_WIDTH / 2.0  # 28.0 mm

# Wheel 1 (Inner / Upper slot) center & bottom saddle height
Z1_CENTER = -78.0         # 78 mm from wall (clears Boost 148 +-74 mm hub & 78 mm tire)
Y1_BOTTOM = -48.0

# Wheel 2 (Outer / Lower J-hook) center & bottom saddle height
Z2_CENTER = -209.0        # 131 mm horizontal offset from Wheel 1 (53 mm gap between two 3.0" tires)
Y2_BOTTOM = -200.0        # 152 mm vertical offset below Wheel 1

OUTER_HOOK_WALL = 8.5     # Outer J-hook wall thickness -> max |Z| = 209 + 28 + 8.5 = 245.5 mm


def build_wheel_holder_29plus() -> bd.Part:
    """Constructs the solid B-Rep CAD model of the 29+ Duroc 50 wheel holder."""
    # Sketch plane: local X = global Z (0 at wall, negative outward),
    #               local Y = global Y (0 at top, negative downward)
    yz = bd.Plane(origin=(0, 0, 0), x_dir=(0, 0, 1), y_dir=(0, 1, 0))

    z1_r = Z1_CENTER + HALF_SLOT   # -50.0
    z1_l = Z1_CENTER - HALF_SLOT   # -106.0
    z2_r = Z2_CENTER + HALF_SLOT   # -181.0
    z2_l = Z2_CENTER - HALF_SLOT   # -237.0
    z2_outer = z2_l - OUTER_HOOK_WALL  # -245.5

    # 1. Outer silhouette in YZ
    with bd.BuildSketch(yz) as outer_sk:
        with bd.BuildLine():
            bd.Line((0.0, -188.0), (0.0, 0.0))                     # Flush wall backplate (188 mm tall)
            bd.Line((0.0, 0.0), (-6.0, 0.0))                       # Top wall pad
            bd.Line((-6.0, 0.0), (-22.0, -15.0))                   # Top screw gusset
            bd.Line((-22.0, -15.0), (-34.0, -15.0))                # Flat outside 3.0" tire envelope
            bd.Line((-34.0, -15.0), (-44.5, -32.0))                # Dip below Wheel 1 3.0" tire sidewall
            bd.Line((-44.5, -32.0), (z1_r, -32.0))                 # Slot 1 inner lip crest (16 mm rim capture)
            bd.Line((z1_r, -32.0), (z1_r, Y1_BOTTOM + 2.5))        # Slot 1 inner vertical pocket wall
            bd.ThreePointArc(                                      # Gently dished 56 mm Duroc 50 saddle
                (z1_r, Y1_BOTTOM + 2.5),
                (Z1_CENTER, Y1_BOTTOM),
                (z1_l, Y1_BOTTOM + 2.5),
            )
            bd.Line((z1_l, Y1_BOTTOM + 2.5), (z1_l, -32.0))        # Slot 1 outer vertical pocket wall
            bd.Line((z1_l, -32.0), (-114.0, -32.0))                # Slot 1 outer lip nose (16 mm rim capture)
            bd.Line((-114.0, -32.0), (-148.0, -163.0))             # Diagonal strut (>22 mm clear of Wheel 2 tire)
            bd.Line((-148.0, -163.0), (-165.0, -185.5))            # Low-slung cantilever neck below Wheel 2 tire
            bd.Line((-165.0, -185.5), (z2_r, -185.5))              # Slot 2 inner lip crest (14.5 mm rim capture)
            bd.Line((z2_r, -185.5), (z2_r, Y2_BOTTOM + 2.5))       # Slot 2 inner pocket wall
            bd.ThreePointArc(                                      # Gently dished 56 mm Duroc 50 saddle
                (z2_r, Y2_BOTTOM + 2.5),
                (Z2_CENTER, Y2_BOTTOM),
                (z2_l, Y2_BOTTOM + 2.5),
            )
            bd.Line((z2_l, Y2_BOTTOM + 2.5), (z2_l, -181.5))       # Slot 2 outer hook inner wall (18.5 mm capture)
            bd.Line((z2_l, -181.5), (z2_outer, -181.5))            # Outer J-hook tip (8.5 mm thick)
            bd.Line((z2_outer, -181.5), (z2_outer, -199.0))        # Outer J-hook back (Z = -245.5 mm)
            bd.ThreePointArc(                                      # 10.5 mm thick bottom arch under Slot 2
                (z2_outer, -199.0),
                (Z2_CENTER, -210.5),
                (-172.5, -199.0),
            )
            bd.Line((-172.5, -199.0), (-144.0, -173.0))            # Tapered underside of cantilever neck
            bd.Line((-144.0, -173.0), (-22.0, -173.0))             # Bottom horizontal truss chord
            bd.Line((-22.0, -173.0), (-6.0, -188.0))               # Bottom screw gusset
            bd.Line((-6.0, -188.0), (0.0, -188.0))                 # Bottom wall pad
        bd.make_face()

        def fillet_outer(z_t: float, y_t: float, r: float) -> None:
            v = min(outer_sk.vertices(), key=lambda vt: math.hypot(vt.X - z_t, vt.Y - y_t))
            dist = math.hypot(v.X - z_t, v.Y - y_t)
            if dist > 2.0:
                raise RuntimeError(f"Expected outer vertex near ({z_t}, {y_t}), closest was ({v.X:.2f}, {v.Y:.2f})")
            bd.fillet(v, r)

        # Gusset & tire-clearance swoop fillets
        fillet_outer(-6.0, 0.0, 10.0)
        fillet_outer(-22.0, -15.0, 18.0)
        fillet_outer(-34.0, -15.0, 8.0)
        fillet_outer(-44.5, -32.0, 4.5)
        # Slot 1 rim lips & R=3.5mm lower corners (clears square-edged 50mm rims cleanly)
        fillet_outer(z1_r, -32.0, 2.0)
        fillet_outer(z1_r, Y1_BOTTOM + 2.5, 3.5)
        fillet_outer(z1_l, Y1_BOTTOM + 2.5, 3.5)
        fillet_outer(z1_l, -32.0, 2.2)
        fillet_outer(-114.0, -32.0, 3.5)
        # Cantilever neck & Slot 2 transitions
        fillet_outer(-148.0, -163.0, 20.0)
        fillet_outer(-165.0, -185.5, 12.0)
        fillet_outer(z2_r, -185.5, 2.2)
        fillet_outer(z2_r, Y2_BOTTOM + 2.5, 3.5)
        fillet_outer(z2_l, Y2_BOTTOM + 2.5, 3.5)
        # Full-round R=4.0mm outer J-hook tip (spoke/tire friendly lead-in)
        fillet_outer(z2_l, -181.5, 4.0)
        fillet_outer(z2_outer, -181.5, 4.0)
        # Underside transitions
        fillet_outer(z2_outer, -199.0, 10.0)
        fillet_outer(-172.5, -199.0, 24.0)
        fillet_outer(-144.0, -173.0, 26.0)
        fillet_outer(-22.0, -173.0, 18.0)
        fillet_outer(-6.0, -188.0, 10.0)

    # 2. Inner triangular truss cutout (maintains 10-15 mm structural wall thickness everywhere)
    with bd.BuildSketch(yz) as inner_sk:
        with bd.BuildLine():
            bd.Line((-10.0, -162.5), (-10.0, -25.0))
            bd.Line((-10.0, -25.0), (-30.0, -25.0))
            bd.Line((-30.0, -25.0), (-41.0, -58.5))
            bd.Line((-41.0, -58.5), (-108.5, -58.5))
            bd.Line((-108.5, -58.5), (-130.0, -162.5))
            bd.Line((-130.0, -162.5), (-10.0, -162.5))
        bd.make_face()

        def fillet_inner(z_t: float, y_t: float, r: float) -> None:
            v = min(inner_sk.vertices(), key=lambda vt: math.hypot(vt.X - z_t, vt.Y - y_t))
            dist = math.hypot(v.X - z_t, v.Y - y_t)
            if dist > 2.0:
                raise RuntimeError(f"Expected inner vertex near ({z_t}, {y_t}), closest was ({v.X:.2f}, {v.Y:.2f})")
            bd.fillet(v, r)

        fillet_inner(-10.0, -25.0, 12.0)
        fillet_inner(-10.0, -162.5, 26.0)
        fillet_inner(-30.0, -25.0, 7.0)
        fillet_inner(-41.0, -58.5, 12.0)
        fillet_inner(-108.5, -58.5, 12.0)
        fillet_inner(-130.0, -162.5, 15.0)

    profile = outer_sk.sketch - inner_sk.sketch

    # 3. Extrude symmetrically along X (-18.0 .. +18.0 = 36.0 mm)
    part = bd.extrude(profile, amount=HALF_WIDTH_X, both=True)

    # 4. 1.0 mm 45-deg chamfers on X = +-18 faces (excluding flush Z=0 wall contact edges)
    side_edges = [
        e for e in part.edges()
        if (abs(e.bounding_box().min.X - HALF_WIDTH_X) < 0.05 and abs(e.bounding_box().max.X - HALF_WIDTH_X) < 0.05)
        or (abs(e.bounding_box().min.X + HALF_WIDTH_X) < 0.05 and abs(e.bounding_box().max.X + HALF_WIDTH_X) < 0.05)
    ]
    chamfer_edges = [
        e for e in side_edges
        if not (abs(e.bounding_box().min.Z) < 0.05 and abs(e.bounding_box().max.Z) < 0.05)
    ]
    part = bd.chamfer(chamfer_edges, length=CHAMFER_X)

    # 5. Wall mounting slotted screw holes (4x8 mm slots at Y=-4..-8 & Y=-180..-184) + 15 mm counterbores
    with bd.BuildSketch(bd.Plane.XY) as hole_sk:
        with bd.Locations((0.0, -6.0), (0.0, -182.0)):
            bd.SlotCenterToCenter(center_separation=4.0, height=4.0, rotation=90)
    part = part - bd.extrude(hole_sk.sketch, amount=-25.0)

    with bd.BuildSketch(bd.Plane.XY.offset(-10.0)) as cb_sk:
        with bd.Locations((0.0, 2.0)):
            bd.SlotCenterToCenter(center_separation=16.0, height=15.0, rotation=90)
        with bd.Locations((0.0, -190.0)):
            bd.SlotCenterToCenter(center_separation=16.0, height=15.0, rotation=90)
    part = part - bd.extrude(cb_sk.sketch, amount=-35.0)

    return part


def export_bambu_3mf(
    stl_path: Path,
    template_3mf_path: Path,
    output_3mf_path: Path,
    bb: bd.BoundBox,
) -> int:
    """
    Packages the tessellated solid into a Bambu Studio .3mf project preserving all print settings
    from `template_3mf_path`, oriented flat on its side and positioned cleanly on a 256x256 plate
    clear of the X1/P1 front-left filament-cutter exclusion zone (0..18 x 0..28).
    """
    import struct

    # Read binary STL triangles and deduplicate vertices for compact, watertight 3MF XML mesh
    with open(stl_path, "rb") as f:
        _header = f.read(80)
        tri_count = struct.unpack("<I", f.read(4))[0]
        raw_data = f.read()

    # Center mesh coordinates at bounding-box center (matching Bambu Studio's native convention)
    cx = 0.5 * (bb.min.X + bb.max.X)
    cy = 0.5 * (bb.min.Y + bb.max.Y)
    cz = 0.5 * (bb.min.Z + bb.max.Z)

    vert_map: dict[tuple[float, float, float], int] = {}
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []

    offset = 0
    for _ in range(tri_count):
        vals = struct.unpack_from("<12fH", raw_data, offset)
        offset += 50
        idxs = []
        for k in range(3):
            vx = round(vals[3 + 3 * k] - cx, 5)
            vy = round(vals[4 + 3 * k] - cy, 5)
            vz = round(vals[5 + 3 * k] - cz, 5)
            key = (vx + 0.0, vy + 0.0, vz + 0.0)
            idx = vert_map.get(key)
            if idx is None:
                idx = len(vertices)
                vert_map[key] = idx
                vertices.append(key)
            idxs.append(idx)
        if idxs[0] != idxs[1] and idxs[1] != idxs[2] and idxs[0] != idxs[2]:
            triangles.append((idxs[0], idxs[1], idxs[2]))

    # Build 3D/Objects/object_1.model XML
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">',
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
        ' <resources>',
        '  <object id="1" p:UUID="00010000-81cb-4c03-9d28-80fed5dfa1dc" type="model">',
        '   <mesh>',
        '    <vertices>',
    ]
    for vx, vy, vz in vertices:
        lines.append(f'     <vertex x="{vx:.6g}" y="{vy:.6g}" z="{vz:.6g}"/>')
    lines.append('    </vertices>')
    lines.append('    <triangles>')
    for v1, v2, v3 in triangles:
        lines.append(f'     <triangle v1="{v1}" v2="{v2}" v3="{v3}"/>')
    lines.extend([
        '    </triangles>',
        '   </mesh>',
        '  </object>',
        ' </resources>',
        ' <build/>',
        '</model>',
    ])
    object_model_xml = "\n".join(lines).encode("utf-8")

    # Compute plate placement transform on 256x256 mm bed:
    # Row-vector transform M maps (X_m, Y_m, Z_m) -> (X_p = Z_m + tx, Y_p = Y_m + ty, Z_p = -X_m + tz)
    # With tx = 128.0: X_p spans [128 - size.Z/2, 128 + size.Z/2] = [5.25, 250.75]
    # With ty = 138.0: Y_p spans [138 - size.Y/2, 138 + size.Y/2] = [32.75, 243.25] (above Y=28 cutter zone!)
    # With tz = HALF_WIDTH_X (18.0): Z_p spans [0.0, 36.0]
    tx, ty, tz = 128.0, 138.0, HALF_WIDTH_X

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        with zipfile.ZipFile(template_3mf_path, "r") as zin:
            zin.extractall(tmp)

        # Write updated object_1.model
        (tmp / "3D" / "Objects" / "object_1.model").write_bytes(object_model_xml)

        # Update build item transform & title in 3D/3dmodel.model
        model_path = tmp / "3D" / "3dmodel.model"
        model_txt = model_path.read_text(encoding="utf-8")
        old_tf = 'transform="-1.69542386e-06 0 -1 0 1 0 1 0 -1.69542386e-06 128 128 18.0001806"'
        new_tf = f'transform="0 0 -1 0 1 0 1 0 0 {tx:.4f} {ty:.4f} {tz:.4f}"'
        if old_tf in model_txt:
            model_txt = model_txt.replace(old_tf, new_tf)
        model_txt = model_txt.replace(
            "<metadata name=\"Title\">Bicycle wheel holder</metadata>",
            "<metadata name=\"Title\">Bicycle wheel holder (29+ Duroc 50)</metadata>",
        )
        model_path.write_text(model_txt, encoding="utf-8")

        # Update face_count & offsets in Metadata/model_settings.config
        ms_path = tmp / "Metadata" / "model_settings.config"
        ms_tree = ET.parse(ms_path)
        ms_root = ms_tree.getroot()
        for elem in ms_root.iter():
            if "face_count" in elem.attrib:
                elem.attrib["face_count"] = str(len(triangles))
            if elem.tag == "metadata" and elem.attrib.get("key") == "name" and elem.attrib.get("value") == "kp8372152.stp":
                elem.attrib["value"] = "Bicycle_wheel_holder_29plus_Duroc50.step"
            if elem.tag == "metadata" and elem.attrib.get("key") == "source_offset_y":
                elem.attrib["value"] = f"{cy:.6f}"
            if elem.tag == "metadata" and elem.attrib.get("key") == "source_offset_z":
                elem.attrib["value"] = f"{cz:.6f}"
            if elem.tag == "assemble_item":
                elem.attrib["transform"] = f"1 0 0 0 1 0 0 0 1 0 10.0 {-cz:.4f}"
        ms_tree.write(ms_path, encoding="utf-8", xml_declaration=True)

        # Repackage .3mf archive
        with zipfile.ZipFile(output_3mf_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for file_path in sorted(tmp.rglob("*")):
                if file_path.is_file():
                    rel = file_path.relative_to(tmp).as_posix()
                    zout.write(file_path, rel)

    return len(triangles)


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    part = build_wheel_holder_29plus()
    bb = part.bounding_box()

    if not part.is_valid or len(part.solids()) != 1:
        raise RuntimeError("Generated CAD part is not a single valid B-Rep solid!")

    step_path = out_dir / "Bicycle_wheel_holder_29plus_Duroc50.step"
    stl_path = out_dir / "Bicycle_wheel_holder_29plus_Duroc50.stl"
    threemf_path = out_dir / "Bicycle_wheel_holder_29plus_Duroc50.3mf"
    template_3mf = out_dir / "Bicycle_wheel_holder.3mf"

    bd.export_step(part, str(step_path))
    bd.export_stl(part, str(stl_path), tolerance=0.015, angular_tolerance=0.08)

    tri_count = 0
    if template_3mf.exists():
        tri_count = export_bambu_3mf(stl_path, template_3mf, threemf_path, bb)

    print("=== 29+ Duroc 50 Wheel Holder Generated Successfully ===")
    print(f"Valid B-Rep Solid : {part.is_valid} (Solids: {len(part.solids())})")
    print(f"Volume            : {part.volume / 1000.0:.2f} cm^3")
    print(f"Dimensions (mm)   : {bb.size.Z:.2f} (depth) x {bb.size.Y:.2f} (height) x {bb.size.X:.2f} (width)")
    print(f"Slot clear width  : {SLOT_WIDTH:.1f} mm (Duroc 50 = 50.0 mm -> 3.0 mm clearance/side)")
    print(f"STEP exported     : {step_path.name}")
    print(f"STL exported      : {stl_path.name}")
    if tri_count:
        print(f"3MF exported      : {threemf_path.name} ({tri_count} triangles)")


if __name__ == "__main__":
    main()
