import cadquery as cq
import math
import os

# ==============================================================================
# 1. CONFIGURATION (ASTM D638 Type II)
# ==============================================================================
# Dimensions based on the user's provided values for Type II.
# All units are in millimeters (mm).
PARAMS = {
    "L_overall": 184.0,    # L0: Total length
    "L_narrow": 57.0,      # L2: Length of the straight narrow section
    "W_narrow": 6.0,       # b2: Width of the narrow section (significantly thinner than Type I)
    "W_grip": 19.0,        # b1: Width of the grip ends
    "Thickness": 3.2,      # h:  Thickness
    "Radius": 114.0,       # r:  Transition radius (larger than Type I)
}

OUTPUT_DIR = r"C:\Users\taner\Downloads"

# ==============================================================================
# 2. GEOMETRY GENERATOR
# ==============================================================================
def generate_astm_type_ii():
    """
    Generates a solid ASTM D638 Type II tensile specimen.
    Calculates the geometry based on the provided L0, L2, and Radius constraints.
    """
    p = PARAMS
    
    # Extract variables for readability
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
    # We calculate the X-distance (dx) required for the radius to bridge
    # the difference in width (dy) tangentially.
    dy = y_grip - y_narrow  # Height difference: (19 - 6) / 2 = 6.5 mm
    
    # Pythagoras: R^2 = dx^2 + (R - dy)^2
    # Solve for dx:
    if rad >= dy:
        dx = math.sqrt(rad**2 - (rad - dy)**2)
    else:
        # Fallback for impossible geometry
        print("Warning: Radius is too small for the requested width change.")
        dx = dy 

    # Define key X-axis coordinates (measured from the center 0,0)
    x_narrow_end = l2 / 2.0          # End of the narrow parallel section
    x_arc_end = x_narrow_end + dx    # End of the curve / Start of the grip
    x_total_end = l0 / 2.0           # Physical end of the specimen

    # --- Sketching ---
    # Draw the top-right quadrant profile
    edge = (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(0, y_narrow)                # Center up to narrow width
        .lineTo(x_narrow_end, y_narrow)     # Draw straight narrow line
        
        # Draw the large transition arc (Concave)
        .radiusArc((x_arc_end, y_grip), -rad) 
        
        .lineTo(x_total_end, y_grip)        # Draw straight grip line
        .lineTo(x_total_end, 0)             # Close to centerline
        .close()
    )

    # --- Solid Creation ---
    # Extrude the profile
    quarter_solid = edge.extrude(thick)
    
    # Mirror YZ (Left side) and XZ (Bottom side)
    # Combining them into one watertight solid
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
    print("Generating ASTM D638 Type II geometry...")
    model = generate_astm_type_ii()

    # Show in editor if available
    if 'show_object' in globals():
        show_object(model, name="ASTM_D638_Type_II")

    # Create directory if missing
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # File paths
    stl_path = os.path.join(OUTPUT_DIR, "ASTM_D638_Type_II_Solid.stl")
    step_path = os.path.join(OUTPUT_DIR, "ASTM_D638_Type_II_Solid.step")
    
    # Export STL (High resolution)
    cq.exporters.export(model, stl_path, tolerance=0.01, angularTolerance=0.05)
    
    # Export STEP
    cq.exporters.export(model, step_path)
    
    print(f"Success! Files saved to:\n- {stl_path}\n- {step_path}")

except Exception as e:
    print(f"An error occurred: {e}")