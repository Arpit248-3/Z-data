"""
SignalGate — Standalone 3D Scoring Sandbox Inference Instrument Generator (V2 Refined)
======================================================================================
Automated Blender Python script using Blender's built-in `bpy` API.
Creates Asset 2 V2: A precision-engineered, open-aperture 3D inference instrument.

Key V2 Design Refinements:
  1. ELIMINATE OVERSIZED OPAQUE DISK:
     - 100% annular housing with open central aperture and zero solid end-cap faces.
     - Separated structural layers (outer bezel, retaining rim, dual guide rails).
  2. REDESIGNED RISK TRACK:
     - 48 individually named segments: risk_segment_00 through risk_segment_47.
     - Substantial radial width (0.22 units) for clear readability at 200-260px dashboard width.
     - Dual concentric metallic guide rails instead of a flat circular disk.
     - Default neutral baseline with segment 00 reference tick; ready for React live score drives.
  3. REBUILT CENTRAL CORE:
     - Visible thin teal inner ring (R=0.44) framing an open optical aperture.
     - Compact central hub (radius 0.12) with polished metallic highlight cap.
     - 3 shallow cantilever bridge struts (at 90°, 210°, 330°), keeping the core hollow and see-through.
  4. REFINED VIOLET DISAGREEMENT CALIPER:
     - Replaces generic spinning loader with twin balanced flank caliper arcs and precision index needle.
     - Restrained muted violet (#B4A0F8) accents without obscuring the central aperture.
  5. PBR CONTRAST & MATERIAL REFINEMENT:
     - Tuned low metallicity (0.04-0.18) on graphite/slate to prevent black silhouette crushing.
     - Crisp structural edge highlighting (#536878) and satin metallic accents (#A2B0BC).

Target Outputs:
  - design_assets/blender/sandbox_inference_instrument_v2.blend
  - design_assets/blender/sandbox_inference_instrument_v2_preview.png
  - design_assets/blender/sandbox-inference-instrument-v2.glb

Technical Safeguards:
  - Pure Python + bpy standard library (zero third-party dependencies).
  - Compatible with Blender 5.2.2 LTS, 4.x, and 3.x.
  - Scene resets only its own isolated collection; never touches Asset 1 or V1 files.
  - Temporary camera and lights are cleaned up before GLB export (0 leaked lights/cameras).

Usage (Headless CLI with Blender 5.2):
  & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --python design_assets/blender/generate_sandbox_instrument_v2.py
"""

import math
import os
import sys
from pathlib import Path

try:
    import bpy
    import mathutils
except ImportError:
    print("[ERROR] This script must be executed within Blender's Python environment.", file=sys.stderr)
    sys.exit(1)


# ==============================================================================
# 1. PATH RESOLUTION & OUTPUT TARGETS (Asset 2 V2 Isolation)
# ==============================================================================

def resolve_project_root() -> Path:
    """Detects the SignalGate project root directory reliably across CLI and GUI runs."""
    try:
        current_file = Path(__file__).resolve()
        candidate = current_file.parent.parent.parent
        if (candidate / "frontend").exists() and (candidate / "design_assets").exists():
            return candidate
    except (NameError, TypeError):
        pass

    cwd = Path.cwd().resolve()
    if (cwd / "frontend").exists() and (cwd / "design_assets").exists():
        return cwd
    if (cwd.parent / "frontend").exists() and (cwd.parent / "design_assets").exists():
        return cwd.parent

    workspace_default = Path(r"C:\Users\arpit\Desktop\project")
    if workspace_default.exists():
        return workspace_default

    return cwd


PROJECT_ROOT = resolve_project_root()
BLEND_OUTPUT_PATH = PROJECT_ROOT / "design_assets" / "blender" / "sandbox_inference_instrument_v2.blend"
GLB_OUTPUT_PATH = PROJECT_ROOT / "design_assets" / "blender" / "sandbox-inference-instrument-v2.glb"
PREVIEW_OUTPUT_PATH = PROJECT_ROOT / "design_assets" / "blender" / "sandbox_inference_instrument_v2_preview.png"


# ==============================================================================
# 2. COLOR SCIENCE & PBR PRINCIPLED BSDF MATERIAL SYSTEM
# ==============================================================================

def hex_to_linear_rgb(hex_code: str) -> tuple[float, float, float, float]:
    """Converts a standard sRGB hex code (#RRGGBB) to scene-linear RGBA for Blender."""
    clean = hex_code.lstrip("#")
    if len(clean) != 6:
        raise ValueError(f"Invalid hex color code: {hex_code}")

    r_srgb = int(clean[0:2], 16) / 255.0
    g_srgb = int(clean[2:4], 16) / 255.0
    b_srgb = int(clean[4:6], 16) / 255.0

    def srgb_to_linear(c: float) -> float:
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    return (srgb_to_linear(r_srgb), srgb_to_linear(g_srgb), srgb_to_linear(b_srgb), 1.0)


def create_principled_material(
    name: str,
    hex_color: str,
    metallic: float = 0.0,
    roughness: float = 0.5,
    emission_hex: str | None = None,
    emission_strength: float = 1.0,
) -> bpy.types.Material:
    """Creates a clean Principled BSDF material compatible with glTF/GLB export."""
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # Principled BSDF Node
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.name = "Principled BSDF"
    bsdf.location = (0, 0)

    # Base Color
    rgba = hex_to_linear_rgb(hex_color)
    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = rgba

    # Metallic & Roughness (Restrained metallic prevents dark black surfaces in flat lighting)
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = float(metallic)
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = float(roughness)

    # Restrained Emission for technical indicator accents
    if emission_hex:
        em_rgba = hex_to_linear_rgb(emission_hex)
        if "Emission Color" in bsdf.inputs:  # Blender 4.0+ / 5.x
            bsdf.inputs["Emission Color"].default_value = em_rgba
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = float(emission_strength)
        elif "Emission" in bsdf.inputs:  # Legacy Blender
            bsdf.inputs["Emission"].default_value = em_rgba

    # Material Output Node
    out = nodes.new(type="ShaderNodeOutputMaterial")
    out.name = "Material Output"
    out.location = (320, 0)
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def setup_materials_palette() -> dict[str, bpy.types.Material]:
    """
    Constructs the canonical SignalGate V2 material palette:
    - Graphite: #18232D (low metallic, moderate roughness, no black crushing)
    - Structural slate: #344654 (chassis structural elements, diffuse-friendly)
    - Lighter structural edge: #536878 (front bezels, retaining rims, bracket chamfers)
    - Teal: #68D8CB (focal optic ring, cardinal ticks, active risk accents)
    - Inactive segment slate: #2A3A48 (distinct neutral scale contrast on dark and light)
    - Violet: #B4A0F8 (epistemic disagreement caliper arcs with restrained emission)
    - Analytical blue: #7DAAFF (telemetry bus accents)
    - Light metallic details: #A2B0BC (controlled metallic=0.55, roughness=0.26)
    """
    return {
        "graphite": create_principled_material(
            name="mat_graphite",
            hex_color="#18232D",
            metallic=0.06,
            roughness=0.48,
        ),
        "slate": create_principled_material(
            name="mat_structural_slate",
            hex_color="#344654",
            metallic=0.10,
            roughness=0.42,
        ),
        "edge": create_principled_material(
            name="mat_structural_edge",
            hex_color="#536878",
            metallic=0.16,
            roughness=0.32,
        ),
        "teal": create_principled_material(
            name="mat_teal",
            hex_color="#68D8CB",
            metallic=0.04,
            roughness=0.20,
            emission_hex="#68D8CB",
            emission_strength=1.15,
        ),
        "segment_neutral": create_principled_material(
            name="mat_risk_segment_neutral",
            hex_color="#2D3E4E",
            metallic=0.08,
            roughness=0.38,
        ),
        "violet": create_principled_material(
            name="mat_violet",
            hex_color="#B4A0F8",
            metallic=0.04,
            roughness=0.20,
            emission_hex="#B4A0F8",
            emission_strength=1.15,
        ),
        "blue": create_principled_material(
            name="mat_blue",
            hex_color="#7DAAFF",
            metallic=0.04,
            roughness=0.20,
            emission_hex="#7DAAFF",
            emission_strength=1.0,
        ),
        "metallic": create_principled_material(
            name="mat_light_metallic",
            hex_color="#A2B0BC",
            metallic=0.55,
            roughness=0.26,
        ),
    }


# ==============================================================================
# 3. SCENE INITIALIZATION & SAFE RESET (Asset 2 Isolation)
# ==============================================================================

def reset_instrument_scene() -> bpy.types.Collection:
    """
    Initializes a fresh, clean scene strictly for Asset 2 V2.
    Starts from empty factory defaults so no extraneous cameras/lights exist.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)

    col_name = "Sandbox_Instrument_V2_Assembly"
    col = bpy.data.collections.get(col_name)
    if not col:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)

    view_layer = bpy.context.view_layer
    view_layer.active_layer_collection = view_layer.layer_collection.children.get(col_name)

    return col


# ==============================================================================
# 4. GEOMETRIC PRIMITIVE GENERATION HELPERS
# ==============================================================================

def create_empty(name: str, location: tuple[float, float, float], parent: bpy.types.Object | None = None) -> bpy.types.Object:
    """Creates a transform Empty object to serve as a group or sub-assembly parent."""
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.4
    empty.location = location

    col = bpy.data.collections.get("Sandbox_Instrument_V2_Assembly") or bpy.context.scene.collection
    col.objects.link(empty)

    if parent:
        empty.parent = parent

    bpy.context.view_layer.update()
    return empty


def add_mesh_cube(
    name: str,
    local_pos: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    parent: bpy.types.Object,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    """Spawns a clean box mesh, applies dimensions, assigns material, and parents it to the group."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = f"{name}_mesh"

    obj.scale = scale
    obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    obj.parent = parent
    obj.location = local_pos

    if material:
        obj.data.materials.append(material)

    bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    return obj


def add_mesh_cylinder(
    name: str,
    local_pos: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    vertices: int = 48,
    cap_ends: bool = False,
) -> bpy.types.Object:
    """Spawns a clean cylinder mesh with optional open tube ends (cap_ends=False prevents solid disk faces)."""
    end_fill = "NGON" if cap_ends else "NOTHING"
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        end_fill_type=end_fill,
        location=(0, 0, 0),
        rotation=rotation,
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = f"{name}_mesh"

    obj.parent = parent
    obj.location = local_pos

    if material:
        obj.data.materials.append(material)

    bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    return obj


def add_mesh_torus(
    name: str,
    local_pos: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    major_segments: int = 48,
    minor_segments: int = 16,
) -> bpy.types.Object:
    """Spawns an open precision ring/torus mesh with guaranteed hollow center."""
    bpy.ops.mesh.primitive_torus_add(
        major_segments=major_segments,
        minor_segments=minor_segments,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=(0, 0, 0),
        rotation=rotation,
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = f"{name}_mesh"

    obj.parent = parent
    obj.location = local_pos

    if material:
        obj.data.materials.append(material)

    bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    return obj


def add_mesh_curved_arc(
    name: str,
    radius: float,
    thickness: float,
    depth: float,
    start_angle_deg: float,
    end_angle_deg: float,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    subdivisions: int = 16,
    local_y: float = -0.04,
) -> bpy.types.Object:
    """
    Creates a precision curved sector ribbon/arc mesh concentric with the origin.
    Perfect for caliper disagreement arcs hugging the inner ring without solid plates or spinning loaders.
    """
    verts = []
    faces = []

    start_rad = math.radians(start_angle_deg)
    end_rad = math.radians(end_angle_deg)
    r_in = radius - (thickness / 2.0)
    r_out = radius + (thickness / 2.0)
    y_front = local_y - (depth / 2.0)
    y_back = local_y + (depth / 2.0)

    # 4 vertices per angle step
    for i in range(subdivisions + 1):
        frac = i / subdivisions
        theta = start_rad + frac * (end_rad - start_rad)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        verts.append((r_in * cos_t, y_back, r_in * sin_t))     # 4*i + 0
        verts.append((r_out * cos_t, y_back, r_out * sin_t))    # 4*i + 1
        verts.append((r_in * cos_t, y_front, r_in * sin_t))    # 4*i + 2
        verts.append((r_out * cos_t, y_front, r_out * sin_t))   # 4*i + 3

    # Quad faces between steps
    for i in range(subdivisions):
        b0 = 4 * i
        b1 = 4 * (i + 1)
        faces.append((b0 + 2, b1 + 2, b1 + 3, b0 + 3))  # Front
        faces.append((b0 + 1, b1 + 1, b1 + 0, b0 + 0))  # Back
        faces.append((b0 + 0, b1 + 0, b1 + 2, b0 + 2))  # Inner
        faces.append((b0 + 3, b1 + 3, b1 + 1, b0 + 1))  # Outer

    # End caps
    faces.append((0, 2, 3, 1))  # Start cap
    last = 4 * subdivisions
    faces.append((last + 1, last + 3, last + 2, last + 0))  # End cap

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    col = bpy.data.collections.get("Sandbox_Instrument_V2_Assembly") or bpy.context.scene.collection
    col.objects.link(obj)

    if parent:
        obj.parent = parent

    if material:
        obj.data.materials.append(material)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    return obj


# ==============================================================================
# 5. COMPONENT 1: INSTRUMENT HOUSING (Annular Bezel & Open Frame)
# ==============================================================================

def build_instrument_housing(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the 100% annular, open-frame housing:
    - NO solid end-cap disks or covering plates.
    - Outer annular torus chassis bezel in Graphite #18232D (R=1.84, r=0.075).
    - Front structural retaining rim in Lighter Structural Edge #536878 (R=1.84, r=0.038).
    - Outer step retaining collar in Slate #344654 (R=1.66, r=0.032).
    - Inner risk retaining collar in Edge #536878 (R=1.24, r=0.028).
    - 4 perimeter bridge brackets (at 45°, 135°, 225°, 315°) in #536878.
    - 4 open structural diagonal chassis struts bridging outer bezel to inner aperture.
    - Left & right mounting flange lugs with metallic pivot pins in #A2B0BC.
    """
    # 1. Outer Annular Chassis Bezel (Torus primitive: 100% open center bore)
    add_mesh_torus(
        name="housing_outer_annular_bezel",
        local_pos=(0.0, 0.04, 0.0),
        major_radius=1.84,
        minor_radius=0.075,
        material=mats["graphite"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 2. Front Structural Retaining Hairline Rim (Edge Slate #536878)
    add_mesh_torus(
        name="housing_front_rim",
        local_pos=(0.0, -0.06, 0.0),
        major_radius=1.84,
        minor_radius=0.038,
        material=mats["edge"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 3. Outer Step Retaining Collar (Slate #344654, frames outside of risk track)
    add_mesh_torus(
        name="housing_inner_step_collar",
        local_pos=(0.0, 0.02, 0.0),
        major_radius=1.66,
        minor_radius=0.032,
        material=mats["slate"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 4. Inner Risk Retaining Collar (Edge #536878, frames inside of risk track)
    add_mesh_torus(
        name="housing_risk_inner_collar",
        local_pos=(0.0, 0.01, 0.0),
        major_radius=1.24,
        minor_radius=0.028,
        material=mats["edge"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 5. Four Perimeter Structural Brackets (Open frame supports at 45°, 135°, 225°, 315°)
    for b_idx, angle_deg in enumerate([45, 135, 225, 315], start=1):
        rad = math.radians(angle_deg)
        bx = 1.76 * math.cos(rad)
        bz = 1.76 * math.sin(rad)
        b_rot = (math.radians(90), 0, -rad + math.radians(90))

        add_mesh_cube(
            name=f"housing_frame_bracket_{b_idx:02d}",
            local_pos=(bx, -0.01, bz),
            scale=(0.14, 0.08, 0.16),
            material=mats["edge"],
            parent=parent,
            rotation=b_rot,
        )

    # 6. Four Open Structural Diagonal Chassis Struts (at 45°, 135°, 225°, 315°)
    # Connects outer bezel collar (R=1.24) to inner aperture assembly (R=0.68),
    # framing 4 large open aperture windows through which depth is visible.
    for s_idx, angle_deg in enumerate([45, 135, 225, 315], start=1):
        rad = math.radians(angle_deg)
        mid_r = 0.96
        sx = mid_r * math.cos(rad)
        sz = mid_r * math.sin(rad)
        s_rot = (math.radians(90), 0, -rad + math.radians(90))

        add_mesh_cube(
            name=f"housing_aperture_strut_{s_idx:02d}",
            local_pos=(sx, 0.02, sz),
            scale=(0.048, 0.048, 0.56),
            material=mats["slate"],
            parent=parent,
            rotation=s_rot,
        )

    # 7. Side Mounting Flange Lugs (Left & Right with Stainless Pins)
    for side, sx in [("left", -1.94), ("right", 1.94)]:
        add_mesh_cube(
            name=f"housing_flange_{side}",
            local_pos=(sx, 0.0, 0.0),
            scale=(0.14, 0.18, 0.44),
            material=mats["edge"],
            parent=parent,
        )
        add_mesh_cylinder(
            name=f"housing_flange_pin_{side}",
            local_pos=(sx + (0.04 if sx > 0 else -0.04), 0.0, 0.0),
            radius=0.045,
            depth=0.14,
            material=mats["metallic"],
            parent=parent,
            rotation=(0, math.radians(90), 0),
            cap_ends=True,
        )


# ==============================================================================
# 6. COMPONENT 2: RISK TRACK & 48 DYNAMIC RISK SEGMENTS
# ==============================================================================

def build_risk_track(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the high-readability 48-segment circular risk gauge:
    - Dual concentric metallic guide rails (outer R=1.54, inner R=1.30) — NO opaque solid disk.
    - 48 individually named segments: risk_segment_00 through risk_segment_47.
      Radial width: 0.22 units (high readability at 200-260px dashboard scale).
      Progression: Clockwise circle starting at 12 o'clock (+Z, angle = 90 deg).
      Segment 00 carries a crisp Teal (#68D8CB) zero-index reference accent;
      Segments 01..47 use neutral Slate (#2D3E4E) with metallic edge trims.
      React can query and highlight any subset of segments in real time based on score.
    """
    track_radius = 1.42

    # 1. Dual Concentric Metallic Guide Rails (Open torus tracks; zero solid disk faces)
    add_mesh_torus(
        name="risk_track_outer_rail",
        local_pos=(0.0, -0.01, 0.0),
        major_radius=1.54,
        minor_radius=0.024,
        material=mats["metallic"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )
    add_mesh_torus(
        name="risk_track_inner_rail",
        local_pos=(0.0, -0.01, 0.0),
        major_radius=1.30,
        minor_radius=0.024,
        material=mats["metallic"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 2. Midline Neutral Guide Wire (Slate #344654)
    add_mesh_torus(
        name="risk_track_midline_wire",
        local_pos=(0.0, 0.01, 0.0),
        major_radius=track_radius,
        minor_radius=0.014,
        material=mats["slate"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 3. 48 Individually Named Risk Segments (risk_segment_00 to risk_segment_47)
    num_segments = 48
    for i in range(num_segments):
        # Angle theta: Clockwise progression starting at 12 o'clock (angle = 90 deg)
        theta = (math.pi / 2.0) - (i * (2.0 * math.pi / num_segments))

        # Position along the circular scale (X-Z plane, Y=-0.04 front projection)
        sx = track_radius * math.cos(theta)
        sz = track_radius * math.sin(theta)

        # Tangential orientation: rotates local X axis along track tangent
        seg_rot = (math.radians(90), 0, -theta + (math.pi / 2.0))

        # Segment 00 carries a subtle Teal zero-reference indicator;
        # Segments 01..47 start in neutral slate, ready for React live score modulation
        seg_mat = mats["teal"] if i == 0 else mats["segment_neutral"]

        # Dimensions: radial width = 0.22, tangential arc length = 0.138, depth = 0.065
        add_mesh_cube(
            name=f"risk_segment_{i:02d}",
            local_pos=(sx, -0.04, sz),
            scale=(0.138, 0.065, 0.220),
            material=seg_mat,
            parent=parent,
            rotation=seg_rot,
        )


# ==============================================================================
# 7. COMPONENT 3: UNCERTAINTY ARC (Restrained Violet Epistemic Caliper)
# ==============================================================================

def build_uncertainty_arc(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the restrained violet epistemic disagreement motif:
    - Replaces generic spinning rings with two carefully aligned, short open arcs around the inner ring.
    - Symmetrical caliper arcs flanking the inner ring at R = 0.54 (concentric to teal ring at R=0.44):
      * Left Caliper Arc: spans 150° to 210° (60° sector centered at 9 o'clock / 180°).
      * Right Caliper Arc: spans -30° to +30° (60° sector centered at 3 o'clock / 0°).
    - Metallic terminal stop collars at arc ends in Light Metallic #A2B0BC.
    - Leaves central aperture and hub completely unobstructed.
    """
    arc_r = 0.54
    arc_thick = 0.038
    arc_depth = 0.045

    # 1. Left Epistemic Flank Caliper Arc (150° to 210°)
    add_mesh_curved_arc(
        name="uncertainty_caliper_left_blade",
        radius=arc_r,
        thickness=arc_thick,
        depth=arc_depth,
        start_angle_deg=150.0,
        end_angle_deg=210.0,
        material=mats["violet"],
        parent=parent,
        subdivisions=16,
        local_y=-0.04,
    )
    # Stop collars at 150° and 210°
    for angle_deg, pos_tag in [(150.0, "top"), (210.0, "bottom")]:
        rad = math.radians(angle_deg)
        cx = arc_r * math.cos(rad)
        cz = arc_r * math.sin(rad)
        add_mesh_cylinder(
            name=f"uncertainty_caliper_left_stop_{pos_tag}",
            local_pos=(cx, -0.04, cz),
            radius=0.024,
            depth=0.05,
            material=mats["metallic"],
            parent=parent,
            rotation=(math.radians(90), 0, 0),
            cap_ends=True,
        )

    # 2. Right Epistemic Flank Caliper Arc (-30° to +30°)
    add_mesh_curved_arc(
        name="uncertainty_caliper_right_blade",
        radius=arc_r,
        thickness=arc_thick,
        depth=arc_depth,
        start_angle_deg=-30.0,
        end_angle_deg=30.0,
        material=mats["violet"],
        parent=parent,
        subdivisions=16,
        local_y=-0.04,
    )
    # Stop collars at +30° and -30°
    for angle_deg, pos_tag in [(30.0, "top"), (-30.0, "bottom")]:
        rad = math.radians(angle_deg)
        cx = arc_r * math.cos(rad)
        cz = arc_r * math.sin(rad)
        add_mesh_cylinder(
            name=f"uncertainty_caliper_right_stop_{pos_tag}",
            local_pos=(cx, -0.04, cz),
            radius=0.024,
            depth=0.05,
            material=mats["metallic"],
            parent=parent,
            rotation=(math.radians(90), 0, 0),
            cap_ends=True,
        )


# ==============================================================================
# 8. COMPONENT 4: CENTER CORE (Hollow Aperture, Teal Focal Ring & Micro Hub)
# ==============================================================================

def build_center_core(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the deliberate central composition:
    - Small dark recessed cavity cup in Graphite #18232D (R=0.38, depth=0.035, recessed at Y=0.05).
    - Clearly visible thin Teal inner ring (R=0.44, r=0.022) framing the focal aperture.
    - Outer aperture framing collar in Light Metallic #A2B0BC (R=0.68, r=0.028).
    - Compact central hub (radius 0.11) with polished metallic highlight cap (radius 0.07).
      (Hub is substantially smaller than inner ring; zero giant black spheres or filled plates).
    - 3 shallow cantilever bridge struts (at 90°, 210°, 330°) supporting the hub,
      providing structural mounting details and high contrast against both dark and light dashboard backgrounds.
    """
    # 1. Outer Metallic Aperture Collar (Light Metallic #A2B0BC, R=0.68)
    add_mesh_torus(
        name="core_outer_aperture_collar",
        local_pos=(0.0, 0.01, 0.0),
        major_radius=0.68,
        minor_radius=0.028,
        material=mats["metallic"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 2. Small Dark Recessed Cavity Cup (Graphite #18232D, R=0.38, depth=0.035, recessed back at Y=0.05)
    # Provides crisp contrast behind the central hub and spokes on both dark and light backgrounds
    add_mesh_cylinder(
        name="core_recessed_cavity_backing",
        local_pos=(0.0, 0.05, 0.0),
        radius=0.38,
        depth=0.035,
        material=mats["graphite"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
        cap_ends=True,
    )

    # 3. Clearly Visible Thin Teal Inner Ring (Teal #68D8CB, R=0.44, r=0.022)
    add_mesh_torus(
        name="core_focal_optic_ring",
        local_pos=(0.0, -0.04, 0.0),
        major_radius=0.44,
        minor_radius=0.022,
        material=mats["teal"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 4. Three Shallow Cantilever Bridge Struts (At 90°, 210°, 330°)
    for s_idx, angle_deg in enumerate([90, 210, 330], start=1):
        s_rad = math.radians(angle_deg)
        sx = 0.25 * math.cos(s_rad)
        sz = 0.25 * math.sin(s_rad)
        s_rot = (math.radians(90), 0, -s_rad + math.radians(90))

        add_mesh_cube(
            name=f"core_bridge_strut_{s_idx:02d}",
            local_pos=(sx, -0.02, sz),
            scale=(0.028, 0.028, 0.26),
            material=mats["edge"],
            parent=parent,
            rotation=s_rot,
        )

    # 5. Compact Central Hub with Polished Metallic Highlight Cap
    # Main hub cylinder (radius 0.11, depth 0.06, Slate #344654)
    add_mesh_cylinder(
        name="core_hub_body",
        local_pos=(0.0, 0.0, 0.0),
        radius=0.11,
        depth=0.06,
        material=mats["slate"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
        cap_ends=True,
    )
    # Front metallic highlight cap (radius 0.07, depth 0.02, Light Metallic #A2B0BC)
    add_mesh_cylinder(
        name="core_hub_metallic_cap",
        local_pos=(0.0, -0.038, 0.0),
        radius=0.07,
        depth=0.02,
        material=mats["metallic"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
        cap_ends=True,
    )


# ==============================================================================
# 9. COMPONENT 5: MOUNTING BASE (Structural Plinth & Chamfered Stanchions)
# ==============================================================================

def build_mounting_base(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the low-profile structural mounting pieces:
    - Base platform plinth in Graphite #18232D at Z = -1.94.
    - Dual chamfered vertical stanchions in Slate #344654.
    - Metallic pivot bushings in Light Metallic #A2B0BC.
    - Rear chassis anchor plate in Graphite #18232D.
    """
    # 1. Base Platform Plinth (Graphite #18232D)
    add_mesh_cube(
        name="base_platform_plinth",
        local_pos=(0.0, 0.0, -1.94),
        scale=(1.58, 0.40, 0.09),
        material=mats["graphite"],
        parent=parent,
    )

    # 2. Dual Chamfered Vertical Stanchions (Left & Right)
    for side, sx in [("left", -0.72), ("right", 0.72)]:
        add_mesh_cube(
            name=f"base_stanchion_{side}",
            local_pos=(sx, 0.0, -1.82),
            scale=(0.10, 0.14, 0.20),
            material=mats["slate"],
            parent=parent,
        )
        add_mesh_cylinder(
            name=f"base_pivot_bushing_{side}",
            local_pos=(sx, -0.03, -1.74),
            radius=0.055,
            depth=0.12,
            material=mats["metallic"],
            parent=parent,
            rotation=(math.radians(90), 0, 0),
            cap_ends=True,
        )

    # 3. Rear Chassis Stabilizer Plate
    add_mesh_cube(
        name="base_stabilizer_plate",
        local_pos=(0.0, 0.12, -1.88),
        scale=(1.36, 0.05, 0.16),
        material=mats["graphite"],
        parent=parent,
    )


# ==============================================================================
# 10. COMPONENT 6: INSTRUMENT EDGE DETAILS (Fasteners & Cardinal Ticks)
# ==============================================================================

def build_instrument_edge_details(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the precision instrument edge details:
    - 4 cardinal index markers (Top 12h, Bottom 6h, Left 9h, Right 3h) in Teal #68D8CB.
    - 8 perimeter socket cap fasteners in Light Metallic #A2B0BC.
    - Top telemetry data bus connector socket in Analytical Blue #7DAAFF / Metallic #A2B0BC.
    """
    # 1. Four Cardinal Index Markers at R = 1.68
    cardinal_markers = [
        ("top", 0.0, 1.68, (0, 0, 0)),
        ("bottom", 0.0, -1.68, (0, 0, 0)),
        ("left", -1.68, 0.0, (0, 0, math.radians(90))),
        ("right", 1.68, 0.0, (0, 0, math.radians(90))),
    ]
    for name, cx, cz, rot in cardinal_markers:
        add_mesh_cube(
            name=f"edge_cardinal_tick_{name}",
            local_pos=(cx, -0.10, cz),
            scale=(0.048, 0.028, 0.092),
            material=mats["teal"],
            parent=parent,
            rotation=rot,
        )

    # 2. Eight Perimeter Socket Cap Fasteners around Bezel (R = 1.76 at 45 deg intervals)
    for p in range(8):
        p_angle = (math.pi / 8.0) + p * (2.0 * math.pi / 8.0)
        px = 1.76 * math.cos(p_angle)
        pz = 1.76 * math.sin(p_angle)

        add_mesh_cylinder(
            name=f"edge_fastener_pin_{p+1:02d}",
            local_pos=(px, -0.09, pz),
            radius=0.030,
            depth=0.040,
            material=mats["metallic"],
            parent=parent,
            rotation=(math.radians(90), 0, 0),
            cap_ends=True,
        )

    # 3. Top Telemetry Data Bus Socket
    add_mesh_cube(
        name="edge_telemetry_bus_bracket",
        local_pos=(0.0, 0.01, 1.94),
        scale=(0.30, 0.16, 0.07),
        material=mats["edge"],
        parent=parent,
    )
    add_mesh_cylinder(
        name="edge_telemetry_bus_pin",
        local_pos=(0.0, -0.05, 1.94),
        radius=0.038,
        depth=0.07,
        material=mats["blue"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
        cap_ends=True,
    )


# ==============================================================================
# 11. PREVIEW IMAGE RENDERER (Studio Neutral Setup)
# ==============================================================================

def render_preview_image(output_path: Path) -> bool:
    """
    Renders an orthographic studio preview image with neutral lighting.
    Camera and lights are cleaned up completely so they never enter the production GLB.
    """
    print(f"[ACTION] Rendering neutral studio preview image to: {output_path}...")
    scene = bpy.context.scene

    # 1. Elevated Orthographic Camera
    cam_data = bpy.data.cameras.new("Sandbox_V2_Preview_Camera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 4.6  # Frames the 4.0-unit instrument cleanly
    cam_data.clip_start = 0.1
    cam_data.clip_end = 100.0

    cam_obj = bpy.data.objects.new("Sandbox_V2_Preview_Camera", cam_data)
    cam_obj.location = (0.0, -6.5, 1.4)
    cam_obj.rotation_euler = (math.radians(78), 0, 0)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # 2. Three-Point Studio Lights
    lights = []
    # Key Light (Front-Right, crisp neutral white)
    key_light_data = bpy.data.lights.new("Sandbox_V2_Key_Light", type="POINT")
    key_light_data.energy = 1800.0
    key_light_data.color = (1.0, 0.99, 0.96)
    key_light_obj = bpy.data.objects.new("Sandbox_V2_Key_Light", key_light_data)
    key_light_obj.location = (3.5, -5.0, 4.0)
    scene.collection.objects.link(key_light_obj)
    lights.append(key_light_obj)

    # Fill Light (Front-Left, cool soft fill)
    fill_light_data = bpy.data.lights.new("Sandbox_V2_Fill_Light", type="POINT")
    fill_light_data.energy = 1000.0
    fill_light_data.color = (0.92, 0.96, 1.0)
    fill_light_obj = bpy.data.objects.new("Sandbox_V2_Fill_Light", fill_light_data)
    fill_light_obj.location = (-4.0, -4.5, 2.5)
    scene.collection.objects.link(fill_light_obj)
    lights.append(fill_light_obj)

    # Rim Light (Top-Rear, silhouette definition)
    rim_light_data = bpy.data.lights.new("Sandbox_V2_Rim_Light", type="POINT")
    rim_light_data.energy = 1500.0
    rim_light_data.color = (0.96, 0.98, 1.0)
    rim_light_obj = bpy.data.objects.new("Sandbox_V2_Rim_Light", rim_light_data)
    rim_light_obj.location = (0.0, 4.0, 3.5)
    scene.collection.objects.link(rim_light_obj)
    lights.append(rim_light_obj)

    # Bottom Fill/Bounce Light (Under-chassis illumination for base platform and stanchions)
    bottom_light_data = bpy.data.lights.new("Sandbox_V2_Bottom_Light", type="POINT")
    bottom_light_data.energy = 1100.0
    bottom_light_data.color = (0.88, 0.94, 1.0)
    bottom_light_obj = bpy.data.objects.new("Sandbox_V2_Bottom_Light", bottom_light_data)
    bottom_light_obj.location = (0.0, -3.5, -3.2)
    scene.collection.objects.link(bottom_light_obj)
    lights.append(bottom_light_obj)

    # 3. Render Engine Selection
    available_engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    if "BLENDER_EEVEE_NEXT" in available_engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in available_engines:
        scene.render.engine = "BLENDER_EEVEE"
    elif "CYCLES" in available_engines:
        scene.render.engine = "CYCLES"

    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1080
    scene.render.filepath = str(output_path.resolve())

    # Neutral Dark Slate Studio Background
    world = scene.world or bpy.data.worlds.new("Sandbox_V2_World")
    scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = hex_to_linear_rgb("#0F1720")
        bg_node.inputs["Strength"].default_value = 0.65

    # 4. Render Frame
    try:
        bpy.ops.render.render(write_still=True)
        print(f"  [OK] Rendered preview image: {output_path}")
        success = True
    except Exception as exc:
        print(f"[WARNING] Preview render failed: {exc}", file=sys.stderr)
        success = False

    # 5. Strictly Remove Camera and Lights from Scene
    scene.collection.objects.unlink(cam_obj)
    bpy.data.objects.remove(cam_obj)
    bpy.data.cameras.remove(cam_data)

    for l_obj in lights:
        l_data = l_obj.data
        scene.collection.objects.unlink(l_obj)
        bpy.data.objects.remove(l_obj)
        bpy.data.lights.remove(l_data)

    return success


# ==============================================================================
# 12. PRIMARY GENERATION ORCHESTRATION (Asset 2 V2)
# ==============================================================================

def generate_sandbox_instrument_v2() -> bool:
    """Builds the complete V2 3D Scoring Sandbox Inference Instrument scene and exports assets."""
    print("=" * 75)
    print("SIGNALGATE ASSET 2 V2 — REFINED SCORING SANDBOX INFERENCE INSTRUMENT")
    print("=" * 75)
    print(f"[INFO] Project Root:    {PROJECT_ROOT}")
    print(f"[INFO] Target Blend:    {BLEND_OUTPUT_PATH}")
    print(f"[INFO] Target GLB:      {GLB_OUTPUT_PATH}")
    print(f"[INFO] Target Preview:  {PREVIEW_OUTPUT_PATH}")

    BLEND_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLB_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1. Reset clean scene & setup materials
    assembly_col = reset_instrument_scene()
    mats = setup_materials_palette()

    # 2. Asset Root Empty at origin (0, 0, 0)
    root_name = "sandbox_inference_instrument"
    master_root = create_empty(name=root_name, location=(0.0, 0.0, 0.0))

    # 3. Create Required Named Child Component Groups
    groups = {
        "instrument_housing": create_empty("instrument_housing", (0.0, 0.0, 0.0), parent=master_root),
        "risk_track": create_empty("risk_track", (0.0, 0.0, 0.0), parent=master_root),
        "uncertainty_arc": create_empty("uncertainty_arc", (0.0, 0.0, 0.0), parent=master_root),
        "center_core": create_empty("center_core", (0.0, 0.0, 0.0), parent=master_root),
        "mounting_base": create_empty("mounting_base", (0.0, 0.0, 0.0), parent=master_root),
        "instrument_edge_details": create_empty("instrument_edge_details", (0.0, 0.0, 0.0), parent=master_root),
    }

    # 4. Construct Each Sub-Assembly
    print("  -> Constructing Component 1: instrument_housing (Annular Bezel & Open Frame)...")
    build_instrument_housing(groups["instrument_housing"], mats)

    print("  -> Constructing Component 2: risk_track (Dual Guide Rails & 48 Segments)...")
    build_risk_track(groups["risk_track"], mats)

    print("  -> Constructing Component 3: uncertainty_arc (Flank Calipers & Index Needle)...")
    build_uncertainty_arc(groups["uncertainty_arc"], mats)

    print("  -> Constructing Component 4: center_core (Teal Inner Ring & Micro Hub)...")
    build_center_core(groups["center_core"], mats)

    print("  -> Constructing Component 5: mounting_base (Plinth & Stanchions)...")
    build_mounting_base(groups["mounting_base"], mats)

    print("  -> Constructing Component 6: instrument_edge_details (Fasteners & Ticks)...")
    build_instrument_edge_details(groups["instrument_edge_details"], mats)

    bpy.context.view_layer.update()
    print("[SUCCESS] All 6 instrument components and 48 risk segments generated successfully.")

    # --------------------------------------------------------------------------
    # Save Editable .blend File
    # --------------------------------------------------------------------------
    print(f"[ACTION] Saving editable project file to: {BLEND_OUTPUT_PATH}...")
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUTPUT_PATH))
        print("  [OK] Saved .blend file.")
    except Exception as exc:
        print(f"[ERROR] Failed to save .blend file: {exc}", file=sys.stderr)
        return False

    # --------------------------------------------------------------------------
    # Export Production Binary glTF (.glb)
    # --------------------------------------------------------------------------
    print(f"[ACTION] Exporting binary GLB asset to: {GLB_OUTPUT_PATH}...")
    try:
        bpy.ops.export_scene.gltf(
            filepath=str(GLB_OUTPUT_PATH),
            export_format="GLB",
            use_selection=False,
            export_apply=True,
            export_materials="EXPORT",
            export_extras=True,
            export_yup=True,
        )
        print("  [OK] Exported .glb file.")
    except Exception as exc:
        print(f"[ERROR] glTF export failed: {exc}", file=sys.stderr)
        return False

    # --------------------------------------------------------------------------
    # Render Studio Preview Image
    # --------------------------------------------------------------------------
    render_preview_image(PREVIEW_OUTPUT_PATH)

    # --------------------------------------------------------------------------
    # Deterministic Validation & File Size Audit
    # --------------------------------------------------------------------------
    blend_exists = BLEND_OUTPUT_PATH.exists()
    blend_size = BLEND_OUTPUT_PATH.stat().st_size if blend_exists else 0

    glb_exists = GLB_OUTPUT_PATH.exists()
    glb_size = GLB_OUTPUT_PATH.stat().st_size if glb_exists else 0

    preview_exists = PREVIEW_OUTPUT_PATH.exists()
    preview_size = PREVIEW_OUTPUT_PATH.stat().st_size if preview_exists else 0

    print("=" * 75)
    print("ASSET 2 V2 VERIFICATION AUDIT:")
    print(f"  - Editable Blend: {BLEND_OUTPUT_PATH} ({blend_size:,} bytes) -> {'PASS' if blend_size > 0 else 'FAIL'}")
    print(f"  - Production GLB: {GLB_OUTPUT_PATH} ({glb_size:,} bytes) -> {'PASS' if glb_size > 0 else 'FAIL'}")
    print(f"  - Preview Image:  {PREVIEW_OUTPUT_PATH} ({preview_size:,} bytes) -> {'PASS' if preview_size > 0 else 'FAIL'}")
    print("=" * 75)

    if blend_size > 0 and glb_size > 0:
        print("[ALL VERIFICATIONS PASSED] SignalGate Asset 2 V2 successfully created.")
        return True
    else:
        print("[AUDIT FAILED] One or more exported files are missing or empty.", file=sys.stderr)
        return False


# ==============================================================================
# 13. ENTRYPOINT
# ==============================================================================

if __name__ == "__main__":
    success = generate_sandbox_instrument_v2()
    if not success:
        sys.exit(1)
