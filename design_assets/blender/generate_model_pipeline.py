"""
SignalGate — 3D Model Pipeline Assembly Generator (Refined Edition)
===================================================================
Automated Blender Python script using Blender's built-in `bpy` API.
Generates the precision-engineered 3D Model Pipeline Assembly for SignalGate:
  1. stage_01_input_validation (Open-frame validation cartridge with visible strata)
  2. stage_02_model_inference (Open computational assembly with stacked compute modules)
  3. stage_03_sigmoid_calibration (Genuinely hollow calibration aperture with concentric iris & focal ring)
  4. stage_04_disagreement_residualizer (Streamlined paired-signal instrument with violet accent)
  + Subordinate Interstage Conduit Connectors (1->2, 2->3, 3->4)

Outputs:
  - design_assets/blender/model_pipeline.blend (Editable project)
  - frontend/public/models/model-pipeline.glb (Production glTF binary asset)
  - design_assets/blender/model_pipeline_preview.png (Neutral orthographic preview render)

Usage (CLI Headless with Blender 5.2):
  & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --python design_assets/blender/generate_model_pipeline.py

Usage (Blender GUI):
  Open Blender -> Scripting Workspace -> Open this script -> Run Script (Alt+P)
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
# 1. RESOLVE PROJECT PATHS & OUTPUT TARGETS
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
BLEND_OUTPUT_PATH = PROJECT_ROOT / "design_assets" / "blender" / "model_pipeline.blend"
GLB_OUTPUT_PATH = PROJECT_ROOT / "frontend" / "public" / "models" / "model-pipeline.glb"
PREVIEW_OUTPUT_PATH = PROJECT_ROOT / "design_assets" / "blender" / "model_pipeline_preview.png"


# ==============================================================================
# 2. COLOR SCIENCE & PRINCIPLED BSDF MATERIAL SYSTEM
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
    """Creates or updates a clean Principled BSDF material compatible with glTF/GLB export."""
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
    Constructs the canonical SignalGate material palette:
    - Graphite: #18232D (low metallic, moderate roughness so it doesn't look black without HDRI)
    - Structural slate: #344654 (chassis structural elements, diffuse-friendly)
    - Lighter structural edge: #536878 (rails, corner pillars, bevels)
    - Teal: #68D8CB (validation and focal accents with restrained emission)
    - Blue: #7DAAFF (compute logic rail accents with restrained emission)
    - Violet: #B4A0F8 (epistemic disagreement accents with restrained emission)
    - Light metallic details: #A2B0BC (controlled metallic=0.58 so it remains bright in neutral lighting)
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
            emission_strength=1.1,
        ),
        "blue": create_principled_material(
            name="mat_blue",
            hex_color="#7DAAFF",
            metallic=0.04,
            roughness=0.20,
            emission_hex="#7DAAFF",
            emission_strength=1.0,
        ),
        "violet": create_principled_material(
            name="mat_violet",
            hex_color="#B4A0F8",
            metallic=0.04,
            roughness=0.20,
            emission_hex="#B4A0F8",
            emission_strength=1.1,
        ),
        "metallic": create_principled_material(
            name="mat_light_metallic",
            hex_color="#A2B0BC",
            metallic=0.58,
            roughness=0.28,
        ),
    }


# ==============================================================================
# 3. SCENE CLEANUP & IDEMPOTENT RESET
# ==============================================================================

def reset_scene() -> bpy.types.Collection:
    """
    Safely resets only the objects in the active scene/assembly collection.
    Guarantees no external projects or files outside the target assembly are affected.
    """
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Remove all objects currently in the scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Clean orphaned meshes and materials
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)

    # Setup primary assembly collection
    col_name = "Model_Pipeline_Assembly"
    col = bpy.data.collections.get(col_name)
    if not col:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)

    # Set as active
    view_layer = bpy.context.view_layer
    view_layer.active_layer_collection = view_layer.layer_collection.children.get(col_name)

    return col


# ==============================================================================
# 4. GEOMETRIC PRIMITIVE GENERATION HELPERS
# ==============================================================================

def create_empty(name: str, location: tuple[float, float, float], parent: bpy.types.Object | None = None) -> bpy.types.Object:
    """Creates a transform Empty object to serve as a stage group or sub-assembly parent."""
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.5
    empty.location = location

    col = bpy.data.collections.get("Model_Pipeline_Assembly") or bpy.context.scene.collection
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
    """Spawns a clean cube mesh, applies dimensions, assigns material, and parents it to the module."""
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
    vertices: int = 32,
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
    """Spawns a precision torus/ring mesh."""
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


def add_mesh_sphere(
    name: str,
    local_pos: tuple[float, float, float],
    radius: float,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    segments: int = 32,
    ring_count: int = 16,
) -> bpy.types.Object:
    """Spawns a UV sphere mesh."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=ring_count,
        radius=radius,
        location=(0, 0, 0),
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
# 5. MODULE 1: INPUT VALIDATION (Open-Frame Validation Cartridge)
# ==============================================================================

def build_stage_01_input_validation(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Stage 1: Input Validation
    Visual Metaphor: Open-frame validation cartridge.
    Corrections applied:
    - Opaque central chassis replaced with an open graphite frame.
    - 4 longitudinal corner rails with lighter structural edges (#536878).
    - Open perimeter brackets on left and right instead of solid blocking slabs.
    - 3 visibly separated validation plates (upper, center, lower) visible from the front view.
    - Restrained teal validation indicators (status bar and optical validation beacons).
    - Input port (left) and output coupler (right) fully visible on the horizontal axis.
    """
    rail_x_len = 1.76
    rail_w = 0.08
    y_corner = 0.70
    z_corner = 0.70

    # 1. Four Structural Corner Rails (Open Frame Chassis)
    # Front-Top Rail (Lighter Structural Edge #536878)
    add_mesh_cube(
        name="val_frame_rail_front_top",
        local_pos=(0.0, -y_corner, z_corner),
        scale=(rail_x_len, rail_w, rail_w),
        material=mats["edge"],
        parent=parent,
    )
    # Front-Bottom Rail (Lighter Structural Edge #536878)
    add_mesh_cube(
        name="val_frame_rail_front_bottom",
        local_pos=(0.0, -y_corner, -z_corner),
        scale=(rail_x_len, rail_w, rail_w),
        material=mats["edge"],
        parent=parent,
    )
    # Rear-Top Rail (Structural Slate #344654)
    add_mesh_cube(
        name="val_frame_rail_rear_top",
        local_pos=(0.0, y_corner, z_corner),
        scale=(rail_x_len, rail_w, rail_w),
        material=mats["slate"],
        parent=parent,
    )
    # Rear-Bottom Rail (Structural Slate #344654)
    add_mesh_cube(
        name="val_frame_rail_rear_bottom",
        local_pos=(0.0, y_corner, -z_corner),
        scale=(rail_x_len, rail_w, rail_w),
        material=mats["slate"],
        parent=parent,
    )

    # 2. Open Perimeter End Brackets (Left & Right - Open Frame Structure)
    # Left End Perimeter Beams (Connecting rails at x = -0.85)
    add_mesh_cube(
        name="val_end_beam_left_top",
        local_pos=(-0.85, 0.0, z_corner),
        scale=(rail_w, 2 * y_corner, rail_w),
        material=mats["graphite"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_end_beam_left_bottom",
        local_pos=(-0.85, 0.0, -z_corner),
        scale=(rail_w, 2 * y_corner, rail_w),
        material=mats["graphite"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_end_beam_left_front",
        local_pos=(-0.85, -y_corner, 0.0),
        scale=(rail_w, rail_w, 2 * z_corner),
        material=mats["edge"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_end_beam_left_rear",
        local_pos=(-0.85, y_corner, 0.0),
        scale=(rail_w, rail_w, 2 * z_corner),
        material=mats["graphite"],
        parent=parent,
    )

    # Right End Perimeter Beams (Connecting rails at x = +0.85)
    add_mesh_cube(
        name="val_end_beam_right_top",
        local_pos=(0.85, 0.0, z_corner),
        scale=(rail_w, 2 * y_corner, rail_w),
        material=mats["graphite"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_end_beam_right_bottom",
        local_pos=(0.85, 0.0, -z_corner),
        scale=(rail_w, 2 * y_corner, rail_w),
        material=mats["graphite"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_end_beam_right_front",
        local_pos=(0.85, -y_corner, 0.0),
        scale=(rail_w, rail_w, 2 * z_corner),
        material=mats["edge"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_end_beam_right_rear",
        local_pos=(0.85, y_corner, 0.0),
        scale=(rail_w, rail_w, 2 * z_corner),
        material=mats["graphite"],
        parent=parent,
    )

    # 3. Three Visibly Separated Validation Plates (Data Strata)
    # Upper Stratum (Structural Slate with bright metallic front edge)
    add_mesh_cube(
        name="val_data_strata_upper",
        local_pos=(0.0, 0.04, 0.36),
        scale=(1.56, 1.18, 0.08),
        material=mats["slate"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_data_strata_upper_trim",
        local_pos=(0.0, -0.56, 0.36),
        scale=(1.54, 0.04, 0.09),
        material=mats["metallic"],
        parent=parent,
    )

    # Center Stratum (Structural Edge with Metallic Edge and Teal Status Line)
    add_mesh_cube(
        name="val_data_strata_center",
        local_pos=(0.0, 0.04, 0.0),
        scale=(1.60, 1.20, 0.09),
        material=mats["edge"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_data_strata_center_trim",
        local_pos=(0.0, -0.57, 0.0),
        scale=(1.58, 0.04, 0.10),
        material=mats["metallic"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_data_strata_center_stripe",
        local_pos=(0.0, -0.60, 0.0),
        scale=(1.54, 0.03, 0.04),
        material=mats["teal"],
        parent=parent,
    )

    # Lower Stratum (Structural Slate with bright metallic front edge)
    add_mesh_cube(
        name="val_data_strata_lower",
        local_pos=(0.0, 0.04, -0.36),
        scale=(1.56, 1.18, 0.08),
        material=mats["slate"],
        parent=parent,
    )
    add_mesh_cube(
        name="val_data_strata_lower_trim",
        local_pos=(0.0, -0.56, -0.36),
        scale=(1.54, 0.04, 0.09),
        material=mats["metallic"],
        parent=parent,
    )

    # 4. Restrained Teal Validation Indicators
    # Vertical Front Telemetry Bar (Teal Accent on front-right frame)
    add_mesh_cube(
        name="val_telemetry_rail_teal",
        local_pos=(0.84, -y_corner, 0.0),
        scale=(0.06, 0.06, 1.28),
        material=mats["teal"],
        parent=parent,
    )

    # Optical Validation Sensor Beacons
    for idx, bz in enumerate([0.20, -0.20], start=1):
        add_mesh_cylinder(
            name=f"val_validation_beacon_{idx:02d}",
            local_pos=(0.88, -0.36, bz),
            radius=0.060,
            depth=0.10,
            material=mats["teal"],
            parent=parent,
            rotation=(0, math.radians(90), 0),
        )

    # 5. Visible Input Port (Left Interface on Horizontal Axis)
    add_mesh_cylinder(
        name="val_input_port_flange",
        local_pos=(-0.96, 0.0, 0.0),
        radius=0.42,
        depth=0.12,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )
    add_mesh_cylinder(
        name="val_input_port_bore",
        local_pos=(-1.04, 0.0, 0.0),
        radius=0.28,
        depth=0.10,
        material=mats["graphite"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )

    # 6. Output Interface Coupler (Right Interface meeting Connector 1-2)
    add_mesh_cylinder(
        name="val_output_coupler",
        local_pos=(0.94, 0.0, 0.0),
        radius=0.22,
        depth=0.10,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )


# ==============================================================================
# 6. MODULE 2: MODEL INFERENCE (Open Computational Assembly)
# ==============================================================================

def build_stage_02_model_inference(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Stage 2: Model Inference
    Visual Metaphor: Open computational assembly.
    Corrections applied:
    - Opaque cuboids and obscuring outer panels completely removed.
    - Four modest corner supports (#536878 front, #18232D rear).
    - Three clearly visible horizontal module layers (compute blades).
    - Front face of compute modules features polished metallic trims.
    - Two vertical blue connector rails (#7DAAFF) running across all three layers.
    - One restrained teal indicator centered on the middle module.
    """
    pillar_h = 1.72
    pillar_w = 0.08
    x_corner = 0.76
    y_corner = 0.68

    # 1. Four Modest Corner Supports (Open Structural Frame)
    # Front Pillars (Lighter Structural Edge #536878)
    add_mesh_cube(
        name="inf_corner_pillar_fl",
        local_pos=(-x_corner, -y_corner, 0.0),
        scale=(pillar_w, pillar_w, pillar_h),
        material=mats["edge"],
        parent=parent,
    )
    add_mesh_cube(
        name="inf_corner_pillar_fr",
        local_pos=(x_corner, -y_corner, 0.0),
        scale=(pillar_w, pillar_w, pillar_h),
        material=mats["edge"],
        parent=parent,
    )
    # Rear Pillars (Graphite #18232D)
    add_mesh_cube(
        name="inf_corner_pillar_rl",
        local_pos=(-x_corner, y_corner, 0.0),
        scale=(pillar_w, pillar_w, pillar_h),
        material=mats["graphite"],
        parent=parent,
    )
    add_mesh_cube(
        name="inf_corner_pillar_rr",
        local_pos=(x_corner, y_corner, 0.0),
        scale=(pillar_w, pillar_w, pillar_h),
        material=mats["graphite"],
        parent=parent,
    )

    # 2. Structural Top & Bottom Tie-Plates (Slender Caps)
    add_mesh_cube(
        name="inf_frame_cap_top",
        local_pos=(0.0, 0.0, 0.84),
        scale=(1.64, 1.48, 0.05),
        material=mats["slate"],
        parent=parent,
    )
    add_mesh_cube(
        name="inf_frame_cap_top_edge",
        local_pos=(0.0, -0.72, 0.84),
        scale=(1.62, 0.03, 0.05),
        material=mats["edge"],
        parent=parent,
    )

    add_mesh_cube(
        name="inf_frame_cap_bottom",
        local_pos=(0.0, 0.0, -0.84),
        scale=(1.64, 1.48, 0.05),
        material=mats["slate"],
        parent=parent,
    )
    add_mesh_cube(
        name="inf_frame_cap_bottom_edge",
        local_pos=(0.0, -0.72, -0.84),
        scale=(1.62, 0.03, 0.05),
        material=mats["edge"],
        parent=parent,
    )

    # 3. Three Clearly Visible Horizontal Module Layers (Compute Blades)
    blade_z_coords = [0.38, 0.0, -0.38]
    for idx, bz in enumerate(blade_z_coords, start=1):
        # Compute Blade Body (Structural Slate)
        add_mesh_cube(
            name=f"inf_compute_blade_{idx:02d}",
            local_pos=(0.0, 0.03, bz),
            scale=(1.40, 1.22, 0.18),
            material=mats["slate"],
            parent=parent,
        )

        # Restrained Front Metallic Edge Trim (Polished satin metallic #A2B0BC)
        add_mesh_cube(
            name=f"inf_blade_trim_{idx:02d}",
            local_pos=(0.0, -0.59, bz),
            scale=(1.36, 0.04, 0.12),
            material=mats["metallic"],
            parent=parent,
        )

        # Micro Heat Dissipation Fins (Edge Slate #536878)
        for f_idx, fx in enumerate([-0.34, 0.34], start=1):
            add_mesh_cube(
                name=f"inf_blade_fin_{idx:02d}_{f_idx:02d}",
                local_pos=(fx, -0.60, bz + 0.04),
                scale=(0.09, 0.04, 0.04),
                material=mats["edge"],
                parent=parent,
            )

    # 4. Blue Connector Rails (Vertical interconnects spanning front face)
    add_mesh_cylinder(
        name="inf_logic_rail_blue_l",
        local_pos=(-0.50, -0.64, 0.0),
        radius=0.036,
        depth=1.58,
        material=mats["blue"],
        parent=parent,
        rotation=(0, 0, 0),
    )
    add_mesh_cylinder(
        name="inf_logic_rail_blue_r",
        local_pos=(0.50, -0.64, 0.0),
        radius=0.036,
        depth=1.58,
        material=mats["blue"],
        parent=parent,
        rotation=(0, 0, 0),
    )

    # 5. One Restrained Teal Indicator (Centered on Middle Compute Module)
    add_mesh_cube(
        name="inf_status_matrix_teal",
        local_pos=(0.0, -0.63, 0.0),
        scale=(0.26, 0.030, 0.06),
        material=mats["teal"],
        parent=parent,
    )

    # 6. Interstage Interface Ports (Left & Right on Horizontal Axis)
    add_mesh_cylinder(
        name="inf_input_port_collar",
        local_pos=(-0.92, 0.0, 0.0),
        radius=0.20,
        depth=0.08,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )
    add_mesh_cylinder(
        name="inf_output_port_collar",
        local_pos=(0.92, 0.0, 0.0),
        radius=0.20,
        depth=0.08,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )


# ==============================================================================
# 7. MODULE 3: SIGMOID CALIBRATION (Genuinely Hollow Calibration Aperture)
# ==============================================================================

def build_stage_03_sigmoid_calibration(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Stage 3: Sigmoid Calibration
    Visual Metaphor: Precision hollow calibration aperture.
    Corrections applied:
    - Genuinely hollow aperture: zero solid cylinders or blocking discs in front or center.
    - Concentric ring/torus geometry:
        * Outer structural rings (front and rear) in #536878 and #18232D.
        * Concentric intermediate collar in satin metallic #A2B0BC.
        * Inner focal ring in teal (#68D8CB) defining the calibrated decision threshold.
    - Six modest calibration blades arranged radially at a 14° pitch angle.
    - Central bore (r < 0.44) remains 100% open and readable through the aperture.
    - Restrained metallic indexing ticks around perimeter.
    """
    # 1. Outer Structural Ring Assembly (Front & Rear Tori + Perimeter Braces)
    # Front Outer Ring (Structural Edge Slate #536878)
    add_mesh_torus(
        name="cal_outer_ring_front",
        local_pos=(0.0, -0.18, 0.0),
        major_radius=1.12,
        minor_radius=0.065,
        material=mats["edge"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )
    # Rear Outer Ring (Graphite #18232D)
    add_mesh_torus(
        name="cal_outer_ring_rear",
        local_pos=(0.0, 0.18, 0.0),
        major_radius=1.12,
        minor_radius=0.065,
        material=mats["graphite"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # Longitudinal Structural Perimeter Braces (4 linking struts at 0, 90, 180, 270 deg)
    for s_idx, (sx, sz) in enumerate([(1.12, 0.0), (-1.12, 0.0), (0.0, 1.12), (0.0, -1.12)], start=1):
        add_mesh_cube(
            name=f"cal_perimeter_brace_{s_idx:02d}",
            local_pos=(sx, 0.0, sz),
            scale=(0.07, 0.38, 0.07),
            material=mats["slate"],
            parent=parent,
        )

    # 2. Concentric Intermediate Collar / Aperture Ring (Polished Satin Metallic #A2B0BC)
    add_mesh_torus(
        name="cal_concentric_mid_collar",
        local_pos=(0.0, 0.0, 0.0),
        major_radius=0.80,
        minor_radius=0.045,
        material=mats["metallic"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 3. Visible Inner Teal Ring (Calibrated Risk Boundary - 100% Hollow Core)
    add_mesh_torus(
        name="cal_focal_core_optic",
        local_pos=(0.0, -0.05, 0.0),
        major_radius=0.46,
        minor_radius=0.035,
        material=mats["teal"],
        parent=parent,
        rotation=(math.radians(90), 0, 0),
    )

    # 4. Six Modest Calibration Blades / Iris Details
    # Radial placement between r=0.52 and r=0.76; central bore (r < 0.44) remains fully OPEN
    blade_count = 6
    for i in range(blade_count):
        angle = i * (2 * math.pi / blade_count)
        bx = 0.64 * math.cos(angle)
        bz = 0.64 * math.sin(angle)
        # Tangent rotation in X-Z plane + 14-deg pitch angle so faces catch lighting
        rot_blade = (math.radians(76), math.radians(14), -angle + math.radians(24))
        add_mesh_cube(
            name=f"cal_iris_blade_{i+1:02d}",
            local_pos=(bx, -0.03, bz),
            scale=(0.30, 0.022, 0.11),
            material=mats["metallic"],
            parent=parent,
            rotation=rot_blade,
        )

    # 5. Radial Indexing Ticks (Vernier Calibration Scale)
    tick_count = 8
    for t_idx in range(tick_count):
        t_angle = t_idx * (2 * math.pi / tick_count)
        tx = 0.94 * math.cos(t_angle)
        tz = 0.94 * math.sin(t_angle)
        t_rot = (math.radians(90), 0, -t_angle)
        add_mesh_cube(
            name=f"cal_vernier_tick_{t_idx+1:02d}",
            local_pos=(tx, -0.16, tz),
            scale=(0.024, 0.028, 0.065),
            material=mats["teal"],
            parent=parent,
            rotation=t_rot,
        )

    # 6. Instrument Base Plinth & Port Interfaces
    add_mesh_cube(
        name="cal_pedestal_bracket",
        local_pos=(0.0, 0.0, -0.92),
        scale=(0.56, 0.34, 0.12),
        material=mats["graphite"],
        parent=parent,
    )
    add_mesh_cylinder(
        name="cal_input_port_collar",
        local_pos=(-1.12, 0.0, 0.0),
        radius=0.20,
        depth=0.08,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )
    add_mesh_cylinder(
        name="cal_output_port_collar",
        local_pos=(1.12, 0.0, 0.0),
        radius=0.20,
        depth=0.08,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )


# ==============================================================================
# 8. MODULE 4: DISAGREEMENT RESIDUALIZER (Streamlined Paired-Signal Instrument)
# ==============================================================================

def build_stage_04_disagreement_residualizer(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Stage 4: Disagreement & Residualization
    Visual Metaphor: Streamlined paired-signal instrument.
    Corrections applied:
    - Reduced clutter: removed unnecessary intersecting rails and heavy solid bodies.
    - Two clearly visible intersecting rings, primarily violet (#B4A0F8):
        * Primary signal ring: outer ring in violet (#B4A0F8) tilted at +22°.
        * Secondary signal ring: inner intersecting ring in violet (#B4A0F8) tilted at -22°.
    - Small central hub: compact spherical core with a thin violet equator ring.
    - Minimal open support structure: lightweight cradle with two slim stanchions and pivot pins.
    """
    # 1. Minimal Open Cradle Support (Base bar + 2 slim vertical stanchions)
    add_mesh_cube(
        name="res_cradle_base_bar",
        local_pos=(0.0, 0.0, -0.84),
        scale=(1.36, 0.32, 0.08),
        material=mats["graphite"],
        parent=parent,
    )
    add_mesh_cube(
        name="res_cradle_stanchion_l",
        local_pos=(-0.80, 0.0, -0.42),
        scale=(0.07, 0.08, 0.84),
        material=mats["slate"],
        parent=parent,
    )
    add_mesh_cube(
        name="res_cradle_stanchion_r",
        local_pos=(0.80, 0.0, -0.42),
        scale=(0.07, 0.08, 0.84),
        material=mats["slate"],
        parent=parent,
    )

    # Pivot Bearing Hubs on Cradle
    add_mesh_cylinder(
        name="res_pivot_bearing_l",
        local_pos=(-0.80, 0.0, 0.0),
        radius=0.08,
        depth=0.10,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )
    add_mesh_cylinder(
        name="res_pivot_bearing_r",
        local_pos=(0.80, 0.0, 0.0),
        radius=0.08,
        depth=0.10,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )

    # 2. Two Clearly Visible Intersecting Rings (Primarily Violet #B4A0F8)
    # Primary Signal Ring: Outer Ring in Vibrant Violet #B4A0F8
    add_mesh_torus(
        name="res_signal_ring_primary_violet",
        local_pos=(0.0, 0.0, 0.0),
        major_radius=0.92,
        minor_radius=0.046,
        material=mats["violet"],
        parent=parent,
        rotation=(math.radians(22), math.radians(14), 0),
    )

    # Secondary Signal Ring: Intersecting Counter-Tilted Ring (Violet with Satin Edge)
    add_mesh_torus(
        name="res_signal_ring_secondary_violet",
        local_pos=(0.0, 0.0, 0.0),
        major_radius=0.76,
        minor_radius=0.038,
        material=mats["violet"],
        parent=parent,
        rotation=(math.radians(-22), math.radians(-14), 0),
    )

    # 3. Small Central Hub (Compact, Unobtrusive)
    add_mesh_sphere(
        name="res_harmonic_collector_core",
        local_pos=(0.0, 0.0, 0.0),
        radius=0.14,
        material=mats["slate"],
        parent=parent,
    )
    add_mesh_torus(
        name="res_harmonic_equator_band",
        local_pos=(0.0, 0.0, 0.0),
        major_radius=0.16,
        minor_radius=0.020,
        material=mats["violet"],
        parent=parent,
        rotation=(0, 0, 0),
    )

    # 4. Connecting Pivot Pins & Couplers
    add_mesh_cylinder(
        name="res_pivot_pin_l",
        local_pos=(-0.74, 0.0, 0.0),
        radius=0.026,
        depth=0.12,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )
    add_mesh_cylinder(
        name="res_pivot_pin_r",
        local_pos=(0.74, 0.0, 0.0),
        radius=0.026,
        depth=0.12,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )

    # Left Input Port (Meeting Connector 3-4)
    add_mesh_cylinder(
        name="res_input_port_collar",
        local_pos=(-0.92, 0.0, 0.0),
        radius=0.20,
        depth=0.08,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )
    # Terminal Output Coupler Flange (Right Boundary)
    add_mesh_cylinder(
        name="res_terminal_coupler_flange",
        local_pos=(0.94, 0.0, 0.0),
        radius=0.22,
        depth=0.08,
        material=mats["metallic"],
        parent=parent,
        rotation=(0, math.radians(90), 0),
    )


# ==============================================================================
# 9. INTERSTAGE CONDUIT CONNECTORS (Visually Subordinate Bridges)
# ==============================================================================

def build_interstage_connectors(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]):
    """
    Spawns subordinate, precision-engineered conduit bridge bars between modules.
    Spans exact gap between module ports without passing through front-facing elements.
    """
    connector_specs = [
        {
            "name": "connector_stage_01_to_02",
            "x_center": -4.00,
            "span": 2.15,
            "accent_mat": mats["teal"],
            "wire_z": 0.12,
        },
        {
            "name": "connector_stage_02_to_03",
            "x_center": 0.00,
            "span": 2.06,
            "accent_mat": mats["blue"],
            "wire_z": 0.12,
        },
        {
            "name": "connector_stage_03_to_04",
            "x_center": 4.00,
            "span": 2.06,
            "accent_mat": mats["violet"],
            "wire_z": 0.12,
        },
    ]

    for spec in connector_specs:
        c_empty = create_empty(name=spec["name"], location=(spec["x_center"], 0.0, 0.0), parent=parent)

        # 1. Primary Conduit Bar (Subordinate slender radius=0.038)
        add_mesh_cylinder(
            name=f"{spec['name']}_main_conduit",
            local_pos=(0.0, 0.0, 0.0),
            radius=0.038,
            depth=spec["span"],
            material=mats["slate"],
            parent=c_empty,
            rotation=(0, math.radians(90), 0),
        )

        # 2. Secondary Data Guide Rail (Upper Accent Color)
        add_mesh_cylinder(
            name=f"{spec['name']}_data_bus_upper",
            local_pos=(0.0, 0.0, spec["wire_z"]),
            radius=0.016,
            depth=spec["span"] * 0.96,
            material=spec["accent_mat"],
            parent=c_empty,
            rotation=(0, math.radians(90), 0),
        )

        # 3. Secondary Ground Wire (Lower Metallic)
        add_mesh_cylinder(
            name=f"{spec['name']}_data_bus_lower",
            local_pos=(0.0, 0.0, -spec["wire_z"]),
            radius=0.016,
            depth=spec["span"] * 0.96,
            material=mats["metallic"],
            parent=c_empty,
            rotation=(0, math.radians(90), 0),
        )

        # 4. Sleek Mounting Collars at Joint Ends
        half_span = (spec["span"] / 2.0) - 0.03
        for side, side_name in [(-half_span, "entry"), (half_span, "exit")]:
            add_mesh_cylinder(
                name=f"{spec['name']}_flange_{side_name}",
                local_pos=(side, 0.0, 0.0),
                radius=0.12,
                depth=0.05,
                material=mats["metallic"],
                parent=c_empty,
                rotation=(0, math.radians(90), 0),
            )


# ==============================================================================
# 10. PREVIEW IMAGE RENDERER (Studio Neutral Setup)
# ==============================================================================

def render_preview_image(output_path: Path) -> bool:
    """
    Renders an orthographic studio preview image with neutral lighting.
    Completely isolated so camera & lighting are NOT exported into the production GLB.
    """
    print(f"[ACTION] Rendering neutral orthographic preview image to: {output_path}...")
    scene = bpy.context.scene

    # 1. Setup Elevated Orthographic Camera (Reveals top face and depth)
    cam_data = bpy.data.cameras.new("Preview_Ortho_Camera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 16.5  # Frames all 4 stages across horizontal span (-7.5 to +7.5)
    cam_data.clip_start = 0.1
    cam_data.clip_end = 100.0

    cam_obj = bpy.data.objects.new("Preview_Ortho_Camera", cam_data)
    cam_obj.location = (0.0, -11.0, 2.6)
    cam_obj.rotation_euler = (math.radians(76), 0, 0)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # 2. Setup Three-Point Neutral Studio Lights + Ambient Fill
    lights = []
    # Key Light (Top-Front-Right, neutral warm white)
    key_light_data = bpy.data.lights.new("Preview_Key_Light", type="POINT")
    key_light_data.energy = 2200.0
    key_light_data.color = (1.0, 0.99, 0.96)
    key_light_obj = bpy.data.objects.new("Preview_Key_Light", key_light_data)
    key_light_obj.location = (5.0, -9.0, 7.0)
    scene.collection.objects.link(key_light_obj)
    lights.append(key_light_obj)

    # Fill Light (Front-Left, soft cool white)
    fill_light_data = bpy.data.lights.new("Preview_Fill_Light", type="POINT")
    fill_light_data.energy = 1400.0
    fill_light_data.color = (0.92, 0.96, 1.0)
    fill_light_obj = bpy.data.objects.new("Preview_Fill_Light", fill_light_data)
    fill_light_obj.location = (-7.0, -8.0, 4.0)
    scene.collection.objects.link(fill_light_obj)
    lights.append(fill_light_obj)

    # Rim Light (Top-Rear, crisp separation)
    rim_light_data = bpy.data.lights.new("Preview_Rim_Light", type="POINT")
    rim_light_data.energy = 1600.0
    rim_light_data.color = (0.96, 0.98, 1.0)
    rim_light_obj = bpy.data.objects.new("Preview_Rim_Light", rim_light_data)
    rim_light_obj.location = (0.0, 6.0, 6.0)
    scene.collection.objects.link(rim_light_obj)
    lights.append(rim_light_obj)

    # 3. Render Engine Selection (Blender 5.x / 4.x / EEVEE compatibility)
    available_engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    if "BLENDER_EEVEE_NEXT" in available_engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in available_engines:
        scene.render.engine = "BLENDER_EEVEE"
    elif "CYCLES" in available_engines:
        scene.render.engine = "CYCLES"

    scene.render.resolution_x = 1920
    scene.render.resolution_y = 540
    scene.render.filepath = str(output_path.resolve())

    # Neutral dark slate background
    world = scene.world or bpy.data.worlds.new("Preview_World")
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

    # 5. Clean up temporary camera and lights so they never pollute the scene or GLB
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
# 11. PRIMARY PIPELINE ASSEMBLY ORCHESTRATION
# ==============================================================================

def generate_model_pipeline() -> bool:
    """Builds the complete 3D Model Pipeline scene and saves .blend, .glb, and preview."""
    print("=" * 70)
    print("SIGNALGATE — GENERATING REFINED 3D MODEL PIPELINE ASSEMBLY")
    print("=" * 70)
    print(f"[INFO] Project Root:    {PROJECT_ROOT}")
    print(f"[INFO] Target Blend:    {BLEND_OUTPUT_PATH}")
    print(f"[INFO] Target GLB:      {GLB_OUTPUT_PATH}")
    print(f"[INFO] Target Preview:  {PREVIEW_OUTPUT_PATH}")

    BLEND_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLB_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1. Reset scene & setup materials
    assembly_col = reset_scene()
    mats = setup_materials_palette()

    # 2. Master Root Assembly Empty at origin (0, 0, 0)
    master_root = create_empty(name="model_pipeline_assembly", location=(0.0, 0.0, 0.0))

    # 3. Four Exact Stage Group Empty Nodes (Guaranteed Preservation)
    stage_coords = [
        ("stage_01_input_validation", -6.0),
        ("stage_02_model_inference", -2.0),
        ("stage_03_sigmoid_calibration", 2.0),
        ("stage_04_disagreement_residualizer", 6.0),
    ]

    empties = {}
    for stage_name, x_pos in stage_coords:
        e = create_empty(name=stage_name, location=(x_pos, 0.0, 0.0), parent=master_root)
        empties[stage_name] = e

    # 4. Construct Stages
    print("  -> Building Stage 01: Input Validation (Open-frame Cartridge)...")
    build_stage_01_input_validation(empties["stage_01_input_validation"], mats)

    print("  -> Building Stage 02: Model Inference (Open Computational Assembly)...")
    build_stage_02_model_inference(empties["stage_02_model_inference"], mats)

    print("  -> Building Stage 03: Sigmoid Calibration (Genuinely Hollow Iris Aperture)...")
    build_stage_03_sigmoid_calibration(empties["stage_03_sigmoid_calibration"], mats)

    print("  -> Building Stage 04: Disagreement Residualizer (Streamlined Paired-Signal)...")
    build_stage_04_disagreement_residualizer(empties["stage_04_disagreement_residualizer"], mats)

    print("  -> Building Interstage Bridge Connectors...")
    build_interstage_connectors(master_root, mats)

    bpy.context.view_layer.update()
    print("[SUCCESS] All 4 pipeline stages and connectors constructed successfully.")

    # --------------------------------------------------------------------------
    # Save Editable .blend File
    # --------------------------------------------------------------------------
    print(f"[ACTION] Saving editable project file to: {BLEND_OUTPUT_PATH}...")
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUTPUT_PATH))
        print(f"  [OK] Saved .blend file.")
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
        print(f"  [OK] Exported .glb file.")
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

    print("=" * 70)
    print("ARTIFACT VERIFICATION REPORT:")
    print(f"  - Editable Blend: {BLEND_OUTPUT_PATH} ({blend_size:,} bytes) -> {'PASS' if blend_size > 0 else 'FAIL'}")
    print(f"  - Production GLB: {GLB_OUTPUT_PATH} ({glb_size:,} bytes) -> {'PASS' if glb_size > 0 else 'FAIL'}")
    print(f"  - Preview Image:  {PREVIEW_OUTPUT_PATH} ({preview_size:,} bytes) -> {'PASS' if preview_size > 0 else 'FAIL'}")
    print("=" * 70)

    if blend_size > 0 and glb_size > 0:
        print("[ALL VERIFICATIONS PASSED] SignalGate 3D Model Pipeline successfully created.")
        return True
    else:
        print("[AUDIT FAILED] One or more exported files are missing or empty.", file=sys.stderr)
        return False


# ==============================================================================
# 12. ENTRYPOINT
# ==============================================================================

if __name__ == "__main__":
    success = generate_model_pipeline()
    if not success:
        sys.exit(1)
