# SignalGate — Phase 10: Asset 2 Sandbox Inference Instrument Generation Report

**Document Version:** 1.0.0  
**Timestamp:** 2026-10-18T10:38:00+05:30  
**Asset Generator:** [`design_assets/blender/generate_sandbox_instrument.py`](file:///C:/Users/arpit/Desktop/project/design_assets/blender/generate_sandbox_instrument.py)  
**Detected Blender Installation:** `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` (Blender 5.2.2 LTS)  
**Target Output Artifacts (Produced Upon Execution):**
- Editable Project: [`design_assets/blender/sandbox_inference_instrument.blend`](file:///C:/Users/arpit/Desktop/project/design_assets/blender/sandbox_inference_instrument.blend)
- Production Binary glTF: [`frontend/public/models/sandbox-inference-instrument.glb`](file:///C:/Users/arpit/Desktop/project/frontend/public/models/sandbox-inference-instrument.glb)
- Studio Preview Image: [`design_assets/blender/sandbox_inference_instrument_preview.png`](file:///C:/Users/arpit/Desktop/project/design_assets/blender/sandbox_inference_instrument_preview.png)

**Asset 1 Preservation Audit:**
- `design_assets/blender/model_pipeline.blend` (243,803 bytes, **Preserved Untouched**)
- `design_assets/blender/model_pipeline_backup.blend` (181,598 bytes, **Preserved Untouched**)
- `design_assets/blender/generate_model_pipeline.py` (47,756 bytes, **Preserved Untouched**)
- `frontend/public/models/model-pipeline.glb` (465,796 bytes, **Preserved Untouched**)

---

## 1. Executive Summary & Design Direction

SignalGate Asset 2 is a dedicated, standalone **3D Scoring Sandbox Inference Instrument**. Engineered specifically for the live interactive scoring sandbox, it serves as an authoritative, precision-crafted financial-security forensic gauge.

### Design Principles & Anti-Pattern Avoidance:
- **No Planetary or Centrifuge Tropes:** Avoids oversized black spheres, planetary orbits, spinning crosshairs, or video game targeting radars.
- **Single Cohesive Silhouette:** A compact, bevelled graphite chassis ($R = 1.86$, depth $0.28$) with restrained depth that reads with clinical clarity at both full and thumbnail dashboard scales.
- **Genuinely Hollow Core:** The central optical bore ($r < 0.36$) is completely open, framed by concentric iris collars and pitched metallic diaphragm blades without opaque blocking disks.
- **Dynamic 48-Segment Scale:** Features 48 individually named segments (`risk_segment_00` to `risk_segment_47`) arranged in a precision circular scale, backed by a recessed neutral channel to enable live React highlighting based on calibrated risk probability $p$.
- **Restrained Epistemic Disagreement:** A distinct paired-ring violet element (`uncertainty_arc`) that acts as an optical caliper rather than a misleading probability fill, acknowledging that residual shift $u_2$ is signed and uncoupled from risk.

---

## 2. Named Component Hierarchy & Geometry Construction

The entire asset is parented to a single root Empty at world origin:

```
sandbox_inference_instrument (Root Empty at Origin 0, 0, 0)
  ├── instrument_housing
  │     ├── housing_bezel_outer
  │     ├── housing_front_rim
  │     ├── housing_rear_casing
  │     ├── housing_flange_left & housing_flange_pin_left
  │     ├── housing_flange_right & housing_flange_pin_right
  │     └── housing_chamber_liner
  ├── risk_track
  │     ├── risk_track_backing_groove (Continuous annular channel)
  │     ├── risk_track_outer_rim (Metallic retaining bezel)
  │     ├── risk_track_inner_rim (Metallic retaining bezel)
  │     └── risk_segment_00 ... risk_segment_47 (48 Individual Meshes)
  ├── uncertainty_arc
  │     ├── uncertainty_signal_ring_primary (Violet #B4A0F8, +14° pitch)
  │     ├── uncertainty_signal_ring_secondary (Violet #B4A0F8, -14° pitch)
  │     ├── uncertainty_caliper_bracket_top & bracket_bottom
  │     └── uncertainty_indicator_needle
  ├── center_core
  │     ├── core_iris_collar (Metallic #A2B0BC, R=0.64)
  │     ├── core_focal_optic_ring (Teal #68D8CB, R=0.42)
  │     ├── core_iris_blade_01 ... core_iris_blade_06 (6 Radial Blades)
  │     ├── core_center_focal_pin (Central hub bead)
  │     └── (Hollow central bore: radius r < 0.36 is 100% open)
  ├── mounting_base
  │     ├── base_platform_plinth (Graphite #18232D at Z = -1.94)
  │     ├── base_stanchion_left & base_stanchion_right
  │     ├── base_pivot_bushing_left & base_pivot_bushing_right
  │     └── base_stabilizer_plate
  └── instrument_edge_details
        ├── edge_cardinal_tick_top (Teal #68D8CB at 12 o'clock)
        ├── edge_cardinal_tick_bottom (Teal #68D8CB at 6 o'clock)
        ├── edge_cardinal_tick_left (Teal #68D8CB at 9 o'clock)
        ├── edge_cardinal_tick_right (Teal #68D8CB at 3 o'clock)
        ├── edge_fastener_pin_01 ... edge_fastener_pin_08 (8 Socket Pins)
        └── edge_telemetry_bus_bracket & edge_telemetry_bus_pin
```

### Component Details:

1. **`instrument_housing` (Bevelled Graphite Chassis):**
   - Outer bezel: Cylinder primitive ($R = 1.86$, depth $0.28$) with 48 radial subdivisions in Graphite `#18232D`.
   - Front retaining rim: Precision torus ($R = 1.84$, tube $r = 0.048$) in Lighter Structural Edge `#536878`.
   - Rear casing collar: Cylinder ($R = 1.78$, depth $0.18$) in Structural Slate `#344654`.
   - Dual lateral mounting lugs with stainless pivot pins in Light Metallic `#A2B0BC`.
   - Interior stepped chamber lining ($R = 1.62$, depth $0.18$) in Graphite `#18232D`.

2. **`risk_track` & 48 Dynamic Segments:**
   - **Continuous Recessed Backing Groove:** Annular torus groove ($R = 1.42$, tube $r = 0.082$) in Structural Slate `#344654` positioned at $Y = -0.04$.
   - **Metallic Retainer Rings:** Concentric inner ($R = 1.30$) and outer ($R = 1.54$) retaining trims in Light Metallic `#A2B0BC` framing the segment track.
   - **48 Individual Segments (`risk_segment_00` to `risk_segment_47`):**
     - Progression: Clockwise circle starting at 12 o'clock ($+Z$ in Blender, angle $90^\circ$).
     - Segment Dimensions: Tangential scale $0.132$, axial depth $0.046$, radial thickness $0.114$.
     - Angular Gap: $7.5^\circ$ total pitch with $5.8^\circ$ segment arc and $1.7^\circ$ visual gap ($27\%$ separation ratio).
     - Material Assignment: Segments `00` to `15` assigned active Teal (`#68D8CB`, emission 1.15) for initial baseline demonstration; segments `16` to `47` assigned neutral inactive slate (`#22303C`).
     - React Capability: Each mesh can be queried and recolored independently via Three.js.

3. **`uncertainty_arc` (Epistemic Violet Signal Caliper):**
   - Primary signal ring: Torus ($R = 0.98$, tube $r = 0.034$) in Violet `#B4A0F8` tilted at $(+14^\circ, +8^\circ)$.
   - Secondary intersecting loop: Torus ($R = 0.84$, tube $r = 0.028$) in Violet `#B4A0F8` tilted at $(-14^\circ, -8^\circ)$.
   - Top and bottom anchor calipers in Light Metallic `#A2B0BC` with a calibrated variance indicator needle.

4. **`center_core` (Hollow Optical Iris Aperture):**
   - Intermediate collar: Torus ($R = 0.64$, tube $r = 0.038$) in Light Metallic `#A2B0BC`.
   - Inner focal core: Torus ($R = 0.42$, tube $r = 0.030$) in Teal `#68D8CB`.
   - 6 radial metallic iris blades ($0.18 \times 0.02 \times 0.064$) pitched at $14^\circ$ to catch specular lighting.
   - Unobstructed circular bore ($r < 0.36$) providing a 100% hollow sightline.
   - Floating central hub bead ($r = 0.08$) in Slate `#344654`.

5. **`mounting_base` (Structural Pedestal):**
   - Base plinth bar ($1.60 \times 0.44 \times 0.10$) in Graphite `#18232D` at $Z = -1.94$.
   - Dual chamfered vertical stanchions ($0.10 \times 0.16 \times 0.22$) in Slate `#344654` with metallic bushings ($r = 0.06$).
   - Rear stabilizer plate in Graphite `#18232D`.

6. **`instrument_edge_details` (Fasteners & Telemetry):**
   - 4 cardinal index markers at $0^\circ, 90^\circ, 180^\circ, 270^\circ$ in Teal `#68D8CB`.
   - 8 perimeter socket cap pins at $45^\circ$ intervals ($R = 1.76$) in Light Metallic `#A2B0BC`.
   - Top telemetry data bus bracket in Edge `#536878` and pin in Analytical Blue `#7DAAFF`.

---

## 3. Material System & Color Science Calibration

All materials use Blender's Principled BSDF with sRGB-to-Linear color space conversion and restrained metallicity to prevent dark black silhouette crushing in standard browser lighting:

| Material Name | Hex Color | Base Linear RGB (sRGB-to-Linear) | Metallic | Roughness | Emission Hex / Strength | Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `mat_graphite` | `#18232D` | `(0.009, 0.017, 0.026)` | **0.06** | **0.50** | None | Outer chassis bezel, plinth, cavity liner |
| `mat_structural_slate` | `#344654` | `(0.034, 0.061, 0.089)` | **0.10** | **0.45** | None | Rear casing collar, stanchions, backing groove |
| `mat_structural_edge` | `#536878` | `(0.087, 0.138, 0.188)` | **0.18** | **0.35** | None | Front retaining rim, side lugs, bus bracket |
| `mat_teal` | `#68D8CB` | `(0.138, 0.687, 0.597)` | **0.04** | **0.20** | `#68D8CB` (1.15) | Active risk segments, focal optic ring, ticks |
| `mat_risk_segment_inactive` | `#22303C` | `(0.016, 0.030, 0.047)` | **0.08** | **0.40** | None | Inactive risk track segments |
| `mat_violet` | `#B4A0F8` | `(0.456, 0.352, 0.939)` | **0.04** | **0.20** | `#B4A0F8` (1.15) | Epistemic uncertainty signal rings & needle |
| `mat_blue` | `#7DAAFF` | `(0.205, 0.402, 1.000)` | **0.04** | **0.20** | `#7DAAFF` (1.00) | Top telemetry data bus pin |
| `mat_light_metallic` | `#A2B0BC` | `(0.361, 0.434, 0.503)` | **0.58** | **0.28** | None | Bezel retainers, iris collar, fasteners, pins |

---

## 4. Technical Safeguards & Scene Isolation

1. **Clean Scene Initialization:**
   The generator starts with `bpy.ops.wm.read_factory_settings(use_empty=True)`, ensuring a completely clean environment with 0 default cubes, cameras, or lights.
2. **Zero Pollution of Asset 1:**
   Asset 1 (`model_pipeline.blend` and `model-pipeline.glb`) is completely untouched. All Asset 2 paths are independently defined.
3. **Studio Preview Isolation:**
   When rendering the studio preview image (`sandbox_inference_instrument_preview.png`), the temporary orthographic camera and 3-point studio lights are unlinked and completely deleted from `bpy.data` before glTF export. **0 leaked cameras or lights exist in the GLB**.
4. **Blender 5.2 / 4.x Principled BSDF Compatibility:**
   Dynamically handles `Emission Color` and `Emission Strength` shader inputs in Blender 5.2/4.x with automatic fallback to legacy `Emission`.
5. **Deterministic glTF Export:**
   Uses canonical `bpy.ops.export_scene.gltf` options with `export_apply=True`, `export_materials='EXPORT'`, `export_extras=True`, and `export_yup=True`.

---

## 5. Execution Commands for Installed Blender (Blender 5.2.2 LTS)

Detected installed binary path:  
`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`

### Headless CLI Execution (PowerShell):
```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python design_assets\blender\generate_sandbox_instrument.py
```

### Headless CLI Execution (Windows Command Prompt - CMD):
```cmd
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python design_assets\blender\generate_sandbox_instrument.py
```

### Interactive GUI Execution:
1. Open Blender 5.2.
2. Navigate to the **Scripting** tab.
3. Open `design_assets/blender/generate_sandbox_instrument.py`.
4. Press **Run Script** (`Alt + P`).

---

## 6. Code Review & Verification Status

- **Syntax & AST Validation:**  
  Executed `python -m py_compile design_assets/blender/generate_sandbox_instrument.py`. Exited with code `0` (clean compilation, zero syntax errors).
- **Execution State:**  
  In strict accordance with instructions (*"Do not execute the generator yet. Do not modify backend or scientific artifacts. Stop after creating and reviewing the generator script."*), the script has **NOT** been run yet.
- **Frontend State:**  
  Zero frontend files have been modified for Asset 2 yet; frontend remains clean on Asset 1.
