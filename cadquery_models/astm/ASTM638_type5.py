import cadquery as cq
import math
import os

# ==============================================================================
# 1. CONFIGURATION (ASTM D638 Type V)
# ==============================================================================
# Dimensions based on the user's provided values for Type V.
# All units are in millimeters (mm).
PARAMS = {
    "L_overall": 63.5,     # L0: Total length (much shorter than Type I)
    "L_narrow": 9.53,      # L2: Length of the straight narrow section
    "W_narrow": 3.18,      # b2: Width of the narrow section
    "W_grip": 9.53,        # b1: Width of the grip ends
    "Thickness": 3.2,      # h:  Thickness (standard thickness)
    "Radius": 12.7,        # r:  Transition radius
}

OUTPUT_DIR = r"C:\Users\taner\Downloads"

# ==============================================================================
# 2. GEOMETRY GENERATOR
# ==============================================================================
def generate_astm_type_v():
    """
    Generates a solid ASTM D638 Type V tensile specimen.
    This uses the same robust parametric logic as Types I and II,
    scaled down to Type V dimensions.
    """
    p = PARAMS
    
    # Extract variables
    l0 = p["L_overall"]
    l2 = p["L_narrow"]
    w_narrow = p["W_narrow"]
    w_grip = p["W_grip"]
    rad = p["Radius"]
    thick = p["Thickness"]

    # Calculate symmetry half-widths
    y_narrow = w_narrow / 2.0
    y_grip = w_grip / 2.0
    
    # --- Geometric Math ---
    # Calculate the horizontal length (dx) of the fillet radius.
    # Vertical distance to bridge:
    dy = y_grip - y_narrow  # (9.53 - 3.18) / 2 = 3.175 mm
    
    # Tangency calculation: R^2 = dx^2 + (R - dy)^2
    if rad >= dy:
        dx = math.sqrt(rad**2 - (rad - dy)**2)
    else:
        print("Warning: Radius is too small for the width change.")
        dx = dy 

    # Define key X-axis coordinates from center (0,0)
    x_narrow_end = l2 / 2.0          # End of parallel section (approx 4.76 mm)
    x_arc_end = x_narrow_end + dx    # Start of grip section
    x_total_end = l0 / 2.0           # End of specimen (31.75 mm)

    # --- Sketching ---
    edge = (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(0, y_narrow)                # Center up to narrow width
        .lineTo(x_narrow_end, y_narrow)     # Straight narrow section
        
        # Draw the transition arc (Concave)
        .radiusArc((x_arc_end, y_grip), -rad) 
        
        .lineTo(x_total_end, y_grip)        # Straight grip section
        .lineTo(x_total_end, 0)             # Close to centerline
        .close()
    )

    # --- Solid Creation ---
    # Extrude
    quarter_solid = edge.extrude(thick)
    
    # Mirror to create full body
    full_solid = (
        quarter_solid
        .mirror("YZ", union=True)
        .mirror("XZ", union=True)
    )

    return full_solid

# ==============================================================================
# 3. EXECUTION AND EXPORT
# ==============================================================================
try:
    print("Generating ASTM D638 Type V geometry...")
    model = generate_astm_type_v()

    # Display in editor
    if 'show_object' in globals():
        show_object(model, name="ASTM_D638_Type_V")

    # Ensure directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # File paths
    stl_path = os.path.join(OUTPUT_DIR, "ASTM_D638_Type_V_Solid.stl")
    step_path = os.path.join(OUTPUT_DIR, "ASTM_D638_Type_V_Solid.step")
    
    # Export
    cq.exporters.export(model, stl_path, tolerance=0.01, angularTolerance=0.05)
    cq.exporters.export(model, step_path)
    
    print(f"Success! Files saved to:\n- {stl_path}\n- {step_path}")

except Exception as e:
    print(f"An error occurred: {e}")