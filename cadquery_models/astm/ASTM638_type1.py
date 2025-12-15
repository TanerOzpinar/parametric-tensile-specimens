import cadquery as cq
import math
import os

# ==============================================================================
# 1. CONFIGURATION (ASTM D638 Type I)
# ==============================================================================
# Dimensions based on the user's provided nominal values.
# All units are in millimeters (mm).
PARAMS = {
    "L_overall": 165.0,    # L0: Total length of the specimen
    "L_narrow": 57.0,      # L2: Length of the straight narrow section
    "W_narrow": 13.0,      # b2: Width of the narrow section
    "W_grip": 19.0,        # b1: Width of the grip ends
    "Thickness": 3.2,      # h:  Thickness of the specimen
    "Radius": 76.0,        # r:  Large transition radius
}

OUTPUT_DIR = r"C:\Users\taner\Downloads"

# ==============================================================================
# 2. GEOMETRY GENERATOR
# ==============================================================================
def generate_astm_type_i():
    """
    Generates a solid ASTM D638 Type I tensile specimen.
    Calculates the transition curve mathematically to ensure tangency.
    """
    p = PARAMS
    
    # Extract dimensions for easier reading
    l0 = p["L_overall"]
    l2 = p["L_narrow"]
    w_narrow = p["W_narrow"]
    w_grip = p["W_grip"]
    rad = p["Radius"]
    thick = p["Thickness"]

    # Calculate half-widths for symmetry around the centerline
    y_narrow = w_narrow / 2.0
    y_grip = w_grip / 2.0
    
    # --- Geometric Calculations 
    # We need to calculate the horizontal length (dx) of the transition arc.
    # The arc connects the narrow width to the grip width using radius R.
    # We use the Pythagorean theorem: R^2 = dx^2 + (R - dy)^2
    
    dy = y_grip - y_narrow  # The vertical step (19 - 13) / 2 = 3.0 mm
    
    # Solve for dx (horizontal distance of the fillet)
    # Ensure the radius is physically large enough to bridge the gap
    if rad >= dy:
        dx = math.sqrt(rad**2 - (rad - dy)**2)
    else:
        # Fallback if radius is too small (mathematically impossible for a tangent arc)
        print("Warning: Radius is too small for the width change. Using linear transition.")
        dx = dy 

    # Define key X-coordinates
    x_narrow_end = l2 / 2.0          # Where the narrow straight section ends
    x_arc_end = x_narrow_end + dx    # Where the curve ends and grip starts
    x_total_end = l0 / 2.0           # The physical end of the specimen

    # --- Sketching the Profile 
    # We draw the top-right quadrant and then mirror it.
    edge = (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(0, y_narrow)                # Start from center, go up to narrow width
        .lineTo(x_narrow_end, y_narrow)     # Draw the parallel narrow section
        
        # Draw the transition arc
        # radiusArc(endPoint, radius). Negative radius implies a concave arc.
        .radiusArc((x_arc_end, y_grip), -rad) 
        
        .lineTo(x_total_end, y_grip)        # Draw the straight grip section
        .lineTo(x_total_end, 0)             # Close the loop back to the X-axis
        .close()
    )

    # --- Extrusion and Mirroring 
    # Extrude the 2D profile to the specified thickness
    quarter_solid = edge.extrude(thick)
    
    # Mirror across YZ plane (creates the left side)
    # Mirror across XZ plane (creates the bottom side)
    # union=True combines them into a single watertight solid
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
    print("Generating ASTM D638 Type I geometry...")
    model = generate_astm_type_i()

    # Display in CadQuery Editor if available
    if 'show_object' in globals():
        show_object(model, name="ASTM_D638_Type_I")

    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Define file paths
    stl_path = os.path.join(OUTPUT_DIR, "ASTM_D638_Type_I_Solid.stl")
    step_path = os.path.join(OUTPUT_DIR, "ASTM_D638_Type_I_Solid.step")
    
    # Export to STL
    cq.exporters.export(model, stl_path, tolerance=0.01, angularTolerance=0.05)
    
    # Export to STEP
    cq.exporters.export(model, step_path)
    
    print(f"Success! Files saved to:\n- {stl_path}\n- {step_path}")

except Exception as e:
    print(f"An error occurred during generation: {e}")