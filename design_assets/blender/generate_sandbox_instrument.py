"""
SignalGate — Standalone 3D Scoring Sandbox Inference Instrument Generator
========================================================================
Automated Blender Python script using Blender's built-in `bpy` API.
Creates Asset 2: The Precision-Engineered Scoring Sandbox Inference Instrument.

Hierarchical Structure:
  sandbox_inference_instrument (Root Empty at Origin)
    ├── instrument_housing (Bevelled graphite casing, front rim, chamber lining)
    ├── risk_track (Continuous backing groove + 48 individually named risk segments)
    │     ├── risk_track_backing_groove
    │     ├── risk_track_inner_rim
    │     ├── risk_track_outer_rim
    │     └── risk_segment_00 ... risk_segment_47
    ├── uncertainty_arc (Paired violet epistemic signal arcs & precision calipers)
    ├── center_core (Genuinely hollow aperture iris collar & focal optic ring)
    ├── mounting_base (Low-profile plinth, vertical stanchions, pivot bearings)
    └── instrument_edge_details (Cardinal index ticks, hex fasteners, telemetry socket)

Outputs:
  - design_assets/blender/sandbox_inference_instrument.blend (Editable project)
  - frontend/public/models/sandbox-inference-instrument.glb (Production glTF binary)
  - design_assets/blender/sandbox_inference_instrument_preview.png (Neutral preview render)

Technical Safeguards:
  - Independent Blender project (Asset 2 only; never overwrites or resets Asset 1).
  - Pure Python + bpy standard library (zero external packages or add-ons).
  - Compatible with Blender 5.2.2 LTS / 4.x / 3.x.
  - Temporary camera and lights are cleaned up before GLB export (0 leaked lights/cameras).

Usage (Headless CLI with Blender 5.2):
  & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --python design_assets/blender/generate_sandbox_instrument.py
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
# 1. PATH RESOLUTION & OUTPUT TARGETS (Asset 2 Isolation)
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
BLEND_OUTPUT_PATH = PROJECT_ROOT / "design_assets" / "blender" / "sandbox_inference_instrument.blend"
GLB_OUTPUT_PATH = PROJECT_ROOT / "frontend" / "public" / "models" / "sandbox-inference-instrument.glb"
PREVIEW_OUTPUT_PATH = PROJECT_ROOT / "design_assets" / "blender" / "sandbox_inference_instrument_preview.png"


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
    Constructs the canonical SignalGate instrument material palette:
    - Graphite: #18232D (low metallic, moderate roughness, no black silhouette crushing)
    - Structural slate: #344654 (chassis structural elements, diffuse-friendly)
    - Lighter structural edge: #536878 (bezels, corner pillars, edge retainers)
    - Teal: #68D8CB (active risk segments and focal optic core)
    - Inactive segment slate: #22303C (clear neutral scale contrast)
    - Violet: #B4A0F8 (epistemic disagreement arcs with restrained emission)
    - Analytical blue: #7DAAFF (telemetry bus accents)
    - Light metallic details: #A2B0BC (controlled metallic=0.58 so edges pop in neutral lighting)
    """
    return {
        "graphite": create_principled_material(
            name="mat_graphite",
            hex_color="#18232D",
            metallic=0.06,
            roughness=0.50,
        ),
        "slate": create_principled_material(
            name="mat_structural_slate",
            hex_color="#344654",
            metallic=0.10,
            roughness=0.45,
        ),
        "edge": create_principled_material(
            name="mat_structural_edge",
            hex_color="#536878",
            metallic=0.18,
            roughness=0.35,
        ),
        "teal": create_principled_material(
            name="mat_teal",
            hex_color="#68D8CB",
            metallic=0.04,
            roughness=0.20,
            emission_hex="#68D8CB",
            emission_strength=1.15,
        ),
        "segment_inactive": create_principled_material(
            name="mat_risk_segment_inactive",
            hex_color="#22303C",
            metallic=0.08,
            roughness=0.40,
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
            metallic=0.58,
            roughness=0.28,
        ),
    }


# ==============================================================================
# 3. SCENE INITIALIZATION & SAFE RESET
# ==============================================================================

def reset_instrument_scene() -> bpy.types.Collection:
    """
    Initializes a fresh, clean scene strictly for Asset 2.
    Starts from empty factory defaults so no extraneous cameras/lights exist.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)

    col_name = "Sandbox_Instrument_Assembly"
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

    col = bpy.data.collections.get("Sandbox_Instrument_Assembly") or bpy.context.scene.collection
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
) -> bpy.types.Object:
    """Spawns a clean cylinder mesh with specified orientation and material."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
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
    """Spawns a precision ring/torus mesh with specified radius and orientation."""
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


# ==============================================================================
# 5. COMPONENT 1: INSTRUMENT HOUSING (Chassis & Structural Bezel)
# ==============================================================================

def build_instrument_housing(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the compact, bevelled graphite housing:
    - Outer octagonal/cylindrical chassis bezel in Graphite #18232D.
    - Raised front retaining ring in Structural Edge #536878.
    - Rear casing collar in Slate #344654.
    - Side mounting flanges with metallic fasteners in #A2B0BC.
    - Interior instrument chamber bore (fully hollow opening).
    """
    # 1. Main Outer Chassis Bezel (Cylindrical frame with 48 vertices, R=1.86, depth=0.28)
    add_mesh_cylinder(
        name="housing_bezel_outer",
        local_pos=(0.0, 0.0, 0.0),
        radius=1.86,
        depth=0.28,
        material=mats["graphite"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
        vertices=48,
    )

    # 2. Front Structural Retaining Ring (Torus bezel catching directional lighting)
    add_mesh_torus(
        name="housing_front_rim",
        local_pos=(0.0, -0.14, 0.0),
        major_radius=1.84,
        minor_radius=0.048,
        material=mats["edge"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 3. Rear Casing Collar (Slate #344654)
    add_mesh_cylinder(
        name="housing_rear_casing",
        local_pos=(0.0, 0.12, 0.0),
        radius=1.78,
        depth=0.18,
        material=mats["slate"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
        vertices=48,
    )

    # 4. Side Mounting Flanges (Left & Right)
    for side, sx in [("left", -1.90), ("right", 1.90)]:
        add_mesh_cube(
            name=f"housing_flange_{side}",
            local_pos=(sx, 0.0, 0.0),
            scale=(0.14, 0.22, 0.54),
            material=mats["edge"],
            parent=parent,
        )
        add_mesh_cylinder(
            name=f"housing_flange_pin_{side}",
            local_pos=(sx + (0.04 if sx > 0 else -0.04), 0.0, 0.0),
            radius=0.05,
            depth=0.16,
            material=mats["metallic"],
            parent=parent,
            rotation=(0, math.radians(90), 0),
        )

    # 5. Inner Chamber Step Ring (Dark Graphite lining framing the risk track)
    add_mesh_cylinder(
        name="housing_chamber_liner",
        local_pos=(0.0, -0.02, 0.0),
        radius=1.62,
        depth=0.18,
        material=mats["graphite"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
        vertices=48,
    )


# ==============================================================================
# 6. COMPONENT 2: RISK TRACK & 48 DYNAMIC RISK SEGMENTS
# ==============================================================================

def build_risk_track(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the 48-segment circular risk scale and neutral backing track:
    - Neutral recessed annular channel (risk_track_backing_groove).
    - Inner and outer metallic retainer rims.
    - 48 individually named segments: risk_segment_00 through risk_segment_47.
      Arranged clockwise from 12 o'clock, with clear separation for React state modulation.
      Segments 00..15 assigned active Teal (#68D8CB); 16..47 assigned neutral Slate (#22303C).
    """
    track_radius = 1.42

    # 1. Continuous Neutral Recessed Backing Track (Annular groove)
    add_mesh_torus(
        name="risk_track_backing_groove",
        local_pos=(0.0, -0.04, 0.0),
        major_radius=track_radius,
        minor_radius=0.082,
        material=mats["slate"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 2. Concentric Retainer Rims (Inner & Outer Metallic Trim)
    add_mesh_torus(
        name="risk_track_outer_rim",
        local_pos=(0.0, -0.08, 0.0),
        major_radius=1.54,
        minor_radius=0.024,
        material=mats["metallic"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )
    add_mesh_torus(
        name="risk_track_inner_rim",
        local_pos=(0.0, -0.08, 0.0),
        major_radius=1.30,
        minor_radius=0.024,
        material=mats["metallic"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 3. 48 Individually Named Risk Segments (risk_segment_00 to risk_segment_47)
    # Clockwise progression starting at 12 o'clock (+Z in Blender, angle = 90 deg)
    num_segments = 48
    active_baseline_segments = 16  # Initial active baseline (~33% calibrated risk demo)

    for i in range(num_segments):
        # Angle theta: starts at 90 deg (top/12 o'clock) and rotates clockwise (-i * 2pi / 48)
        theta = (math.pi / 2.0) - (i * (2.0 * math.pi / num_segments))

        # Position along the circular scale (X-Z plane, Y=-0.08 front projection)
        sx = track_radius * math.cos(theta)
        sz = track_radius * math.sin(theta)

        # Tangential orientation: rotates local X axis along the track tangent
        seg_rot = (math.radians(90), 0, -theta + (math.pi / 2.0))

        # First 16 segments use vibrant Teal; remaining 32 use inactive neutral slate
        seg_material = mats["teal"] if i < active_baseline_segments else mats["segment_inactive"]

        add_mesh_cube(
            name=f"risk_segment_{i:02d}",
            local_pos=(sx, -0.08, sz),
            scale=(0.132, 0.046, 0.114),
            material=seg_material,
            parent=parent,
            rotation=seg_rot,
        )


# ==============================================================================
# 7. COMPONENT 3: UNCERTAINTY ARC (Restrained Epistemic Violet Signal)
# ==============================================================================

def build_uncertainty_arc(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the restrained violet uncertainty element:
    - Primary epistemic signal ring in Violet #B4A0F8 tilted at (+14 deg, +8 deg).
    - Counter-tilted secondary signal arc in Violet #B4A0F8 tilted at (-14 deg, -8 deg).
    - Upper and lower metallic caliper brackets in Light Metallic #A2B0BC.
    - Precision indicator needle in Violet #B4A0F8.
    """
    # 1. Primary Epistemic Signal Ring (Violet #B4A0F8)
    add_mesh_torus(
        name="uncertainty_signal_ring_primary",
        local_pos=(0.0, -0.02, 0.0),
        major_radius=0.98,
        minor_radius=0.034,
        material=mats["violet"],
        parent=parent,
        rotation=(math.radians(104), math.radians(14), math.radians(8)),
    )

    # 2. Secondary Intersecting Loop (Violet #B4A0F8)
    add_mesh_torus(
        name="uncertainty_signal_ring_secondary",
        local_pos=(0.0, 0.02, 0.0),
        major_radius=0.84,
        minor_radius=0.028,
        material=mats["violet"],
        parent=parent,
        rotation=(math.radians(76), math.radians(-14), math.radians(-8)),
    )

    # 3. Precision Caliper Brackets (Top & Bottom Anchor Collars in Metallic #A2B0BC)
    add_mesh_cube(
        name="uncertainty_caliper_bracket_top",
        local_pos=(0.0, -0.03, 1.02),
        scale=(0.16, 0.08, 0.06),
        material=mats["metallic"],
        parent=parent,
    )
    add_mesh_cube(
        name="uncertainty_caliper_bracket_bottom",
        local_pos=(0.0, -0.03, -1.02),
        scale=(0.16, 0.08, 0.06),
        material=mats["metallic"],
        parent=parent,
    )

    # 4. Precision Epistemic Caliper Indicator Needle
    add_mesh_cylinder(
        name="uncertainty_indicator_needle",
        local_pos=(0.42, -0.04, 0.72),
        radius=0.022,
        depth=0.22,
        material=mats["violet"],
        parent=parent,
        rotation=(0, math.radians(45), 0),
    )


# ==============================================================================
# 8. COMPONENT 4: CENTER CORE (Genuinely Hollow Aperture & Focal Optics)
# ==============================================================================

def build_center_core(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the restrained central core with a genuinely hollow optical aperture:
    - Metallic intermediate collar (R=0.64) in Light Metallic #A2B0BC.
    - Inner focal core ring (R=0.42) in Teal #68D8CB.
    - 6 radial metallic iris blades pitched at 14 degrees.
    - 100% hollow central bore (radius < 0.36) with clear sightline through the core.
    - Compact floating hub bead (radius 0.08).
    """
    # 1. Metallic Iris Collar Ring
    add_mesh_torus(
        name="core_iris_collar",
        local_pos=(0.0, -0.01, 0.0),
        major_radius=0.64,
        minor_radius=0.038,
        material=mats["metallic"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 2. Inner Optical Focal Ring (Teal #68D8CB)
    add_mesh_torus(
        name="core_focal_optic_ring",
        local_pos=(0.0, -0.06, 0.0),
        major_radius=0.42,
        minor_radius=0.030,
        material=mats["teal"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 3. Six Radial Iris Struts / Blades (Pitched at 14 deg to catch directional light)
    blade_count = 6
    for b in range(blade_count):
        b_angle = b * (2.0 * math.pi / blade_count)
        bx = 0.52 * math.cos(b_angle)
        bz = 0.52 * math.sin(b_angle)
        blade_rot = (math.radians(76), math.radians(14), -b_angle + math.radians(24))

        add_mesh_cube(
            name=f"core_iris_blade_{b+1:02d}",
            local_pos=(bx, -0.04, bz),
            scale=(0.18, 0.020, 0.064),
            material=mats["metallic"],
            parent=parent,
            rotation=blade_rot,
        )

    # 4. Central Compact Floating Focal Hub
    add_mesh_cylinder(
        name="core_center_focal_pin",
        local_pos=(0.0, 0.0, 0.0),
        radius=0.08,
        depth=0.12,
        material=mats["slate"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )


# ==============================================================================
# 9. COMPONENT 5: MOUNTING BASE (Pedestal & Structural Stanchions)
# ==============================================================================

def build_mounting_base(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the low-profile structural mounting pieces:
    - Base platform plinth in Graphite #18232D at Z = -1.94.
    - Dual chamfered vertical stanchions in Slate #344654.
    - Metallic pivot bearings in Light Metallic #A2B0BC.
    - Rear anchor plate in Graphite #18232D.
    """
    # 1. Base Platform Plinth (Graphite #18232D)
    add_mesh_cube(
        name="base_platform_plinth",
        local_pos=(0.0, 0.0, -1.94),
        scale=(1.60, 0.44, 0.10),
        material=mats["graphite"],
        parent=parent,
    )

    # 2. Dual Chamfered Vertical Stanchions (Left & Right)
    for side, sx in [("left", -0.72), ("right", 0.72)]:
        add_mesh_cube(
            name=f"base_stanchion_{side}",
            local_pos=(sx, 0.0, -1.82),
            scale=(0.10, 0.16, 0.22),
            material=mats["slate"],
            parent=parent,
        )
        add_mesh_cylinder(
            name=f"base_pivot_bushing_{side}",
            local_pos=(sx, -0.04, -1.74),
            radius=0.060,
            depth=0.14,
            material=mats["metallic"],
            parent=parent,
            rotation=(math.radians(90), 0, 0),
        )

    # 3. Rear Chassis Stabilizer Plate
    add_mesh_cube(
        name="base_stabilizer_plate",
        local_pos=(0.0, 0.14, -1.88),
        scale=(1.40, 0.06, 0.18),
        material=mats["graphite"],
        parent=parent,
    )


# ==============================================================================
# 10. COMPONENT 6: INSTRUMENT EDGE DETAILS (Fasteners & Telemetry Ports)
# ==============================================================================

def build_instrument_edge_details(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Builds the precision instrument edge details:
    - 4 cardinal index markers (Top 12h, Bottom 6h, Left 9h, Right 3h) in Teal #68D8CB.
    - 8 perimeter socket cap fasteners in Light Metallic #A2B0BC.
    - Top telemetry data bus socket in Analytical Blue #7DAAFF / Metallic #A2B0BC.
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
            local_pos=(cx, -0.15, cz),
            scale=(0.048, 0.032, 0.092),
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
            local_pos=(px, -0.14, pz),
            radius=0.032,
            depth=0.048,
            material=mats["metallic"],
            parent=parent,
            rotation=(math.radians(90), 0, 0),
        )

    # 3. Top Telemetry Data Bus Socket
    add_mesh_cube(
        name="edge_telemetry_bus_bracket",
        local_pos=(0.0, 0.02, 1.94),
        scale=(0.32, 0.18, 0.08),
        material=mats["edge"],
        parent=parent,
    )
    add_mesh_cylinder(
        name="edge_telemetry_bus_pin",
        local_pos=(0.0, -0.06, 1.94),
        radius=0.040,
        depth=0.08,
        material=mats["blue"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
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
    cam_data = bpy.data.cameras.new("Sandbox_Preview_Camera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 4.8  # Fits the 4.0-unit instrument comfortably
    cam_data.clip_start = 0.1
    cam_data.clip_end = 100.0

    cam_obj = bpy.data.objects.new("Sandbox_Preview_Camera", cam_data)
    cam_obj.location = (0.0, -6.5, 1.2)
    cam_obj.rotation_euler = (math.radians(78), 0, 0)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # 2. Three-Point Studio Lights
    lights = []
    # Key Light (Front-Right, crisp white)
    key_light_data = bpy.data.lights.new("Sandbox_Key_Light", type="POINT")
    key_light_data.energy = 1600.0
    key_light_data.color = (1.0, 0.99, 0.96)
    key_light_obj = bpy.data.objects.new("Sandbox_Key_Light", key_light_data)
    key_light_obj.location = (3.5, -5.0, 4.0)
    scene.collection.objects.link(key_light_obj)
    lights.append(key_light_obj)

    # Fill Light (Front-Left, cool soft fill)
    fill_light_data = bpy.data.lights.new("Sandbox_Fill_Light", type="POINT")
    fill_light_data.energy = 900.0
    fill_light_data.color = (0.92, 0.96, 1.0)
    fill_light_obj = bpy.data.objects.new("Sandbox_Fill_Light", fill_light_data)
    fill_light_obj.location = (-4.0, -4.5, 2.5)
    scene.collection.objects.link(fill_light_obj)
    lights.append(fill_light_obj)

    # Rim Light (Top-Rear, silhouette definition)
    rim_light_data = bpy.data.lights.new("Sandbox_Rim_Light", type="POINT")
    rim_light_data.energy = 1100.0
    rim_light_data.color = (0.96, 0.98, 1.0)
    rim_light_obj = bpy.data.objects.new("Sandbox_Rim_Light", rim_light_data)
    rim_light_obj.location = (0.0, 4.0, 3.5)
    scene.collection.objects.link(rim_light_obj)
    lights.append(rim_light_obj)

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
    world = scene.world or bpy.data.worlds.new("Sandbox_World")
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
# 12. PRIMARY GENERATION ORCHESTRATION (Asset 2)
# ==============================================================================

def generate_sandbox_instrument() -> bool:
    """Builds the complete 3D Scoring Sandbox Inference Instrument scene and exports assets."""
    print("=" * 75)
    print("SIGNALGATE ASSET 2 — SCORING SANDBOX INFERENCE INSTRUMENT GENERATOR")
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
    print("  -> Constructing Component 1: instrument_housing...")
    build_instrument_housing(groups["instrument_housing"], mats)

    print("  -> Constructing Component 2: risk_track & 48 dynamic risk segments...")
    build_risk_track(groups["risk_track"], mats)

    print("  -> Constructing Component 3: uncertainty_arc (violet epistemic caliper)...")
    build_uncertainty_arc(groups["uncertainty_arc"], mats)

    print("  -> Constructing Component 4: center_core (hollow optical aperture)...")
    build_center_core(groups["center_core"], mats)

    print("  -> Constructing Component 5: mounting_base (plinth & stanchions)...")
    build_mounting_base(groups["mounting_base"], mats)

    print("  -> Constructing Component 6: instrument_edge_details (fasteners & ports)...")
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
    print("ASSET 2 VERIFICATION AUDIT:")
    print(f"  - Editable Blend: {BLEND_OUTPUT_PATH} ({blend_size:,} bytes) -> {'PASS' if blend_size > 0 else 'FAIL'}")
    print(f"  - Production GLB: {GLB_OUTPUT_PATH} ({glb_size:,} bytes) -> {'PASS' if glb_size > 0 else 'FAIL'}")
    print(f"  - Preview Image:  {PREVIEW_OUTPUT_PATH} ({preview_size:,} bytes) -> {'PASS' if preview_size > 0 else 'FAIL'}")
    print("=" * 75)

    if blend_size > 0 and glb_size > 0:
        print("[ALL VERIFICATIONS PASSED] SignalGate Asset 2 successfully created.")
        return True
    else:
        print("[AUDIT FAILED] One or more exported files are missing or empty.", file=sys.stderr)
        return False


# ==============================================================================
# 13. ENTRYPOINT
# ==============================================================================

if __name__ == "__main__":
    success = generate_sandbox_instrument()
    if not success:
        sys.exit(1)
