import cadquery as cq
import math
import os

# ==============================================================================
# 1. PARAMETERS
# ==============================================================================
params = {
    # --- Specimen Geometry (ISO 527-2 Type 1B) ---
    "overall_length": 150.0,
    "gauge_length": 110.0,
    "parallel_length": 60.0,
    "gauge_width": 10.0,
    "tab_width": 20.0,
    "thickness": 4.0,
    "transition_radius": 60.0,
    
    # --- Lattice Settings ---
    "unit_cell_size": 4.0,       # Cell size (matches thickness for clean edges)
    "strut_radius": 0.5,         # Radius of lattice struts
    "perimeter_wall": 0.8,       # Thickness of the solid side walls
}

# ==============================================================================
# 2. HELPER: FAST LATTICE GENERATION
# ==============================================================================
def create_bcc_lattice_block(cell_size, strut_radius, nx, ny, nz):
    """
    Generates a large block of BCC lattice structure as a single Compound.
    Optimized for performance using makeCylinder.
    """
    s = cell_size / 2.0
    # BCC vectors (Center to 8 corners)
    directions = [
        (s, s, s), (s, s, -s), (s, -s, s), (s, -s, -s),
        (-s, s, s), (-s, s, -s), (-s, -s, s), (-s, -s, -s)
    ]
    
    solids = []
    
    # Calculate offset to center the grid around (0,0)
    offset_x = -((nx - 1) * cell_size) / 2
    offset_y = -((ny - 1) * cell_size) / 2
    
    # Generate struts
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                cx = offset_x + i * cell_size
                cy = offset_y + j * cell_size
                # Start Z at half cell size to center in the layer
                cz = (cell_size / 2.0) + k * cell_size 
                
                center_pt = cq.Vector(cx, cy, cz)
                
                for d in directions:
                    dir_vec = cq.Vector(d)
                    length = abs(dir_vec)
                    
                    # Create geometric cylinder
                    c = cq.Solid.makeCylinder(strut_radius, length, center_pt, dir_vec)
                    solids.append(c)
                    
    # Combine all struts into one lightweight Compound object
    return cq.Compound.makeCompound(solids)

# ==============================================================================
# 3. MAIN GEOMETRY GENERATOR
# ==============================================================================
def generate_open_lattice_specimen(p):
    # --- A. Extract Dimensions ---
    L_total = p["overall_length"]
    W_narrow = p["gauge_width"]
    W_grip = p["tab_width"]
    L_parallel = p["parallel_length"]
    R = p["transition_radius"]
    H = p["thickness"]
    
    y_narrow = W_narrow / 2.0
    y_grip = W_grip / 2.0
    dy = y_grip - y_narrow
    dx = math.sqrt(R**2 - (R - dy)**2)
    x_start_arc = L_parallel / 2.0
    x_end_arc = x_start_arc + dx
    x_total = L_total / 2.0

    print("[INFO] Step 1: Generating base profile...")
    
    # Create the 2D Profile (Wire)
    base_sketch = (
        cq.Workplane("XY")
        .moveTo(x_start_arc, y_narrow)
        .radiusArc((x_end_arc, y_grip), -R)
        .lineTo(x_total, y_grip)
        .lineTo(x_total, -y_grip)
        .lineTo(x_end_arc, -y_grip)
        .radiusArc((x_start_arc, -y_narrow), -R)
        .lineTo(-x_start_arc, -y_narrow)
        .radiusArc((-x_end_arc, -y_grip), -R)
        .lineTo(-x_total, -y_grip)
        .lineTo(-x_total, y_grip)
        .lineTo(-x_end_arc, y_grip)
        .radiusArc((-x_start_arc, y_narrow), -R)
        .close()
    )
    
    print("[INFO] Step 2: Creating Frame and Core Volume...")

    # 1. Create Full Solid Block (Reference)
    full_block = base_sketch.extrude(H)
    
    # 2. Calculate Offset Wires (Inner boundary)
    # Using 'intersection' mode to handle topology changes if neck is thin
    try:
        offset_wires_obj = base_sketch.val().offset2D(-p["perimeter_wall"], kind="intersection")
    except Exception as e:
        print(f"[ERROR] Offset failed: {e}. Returning solid block.")
        return full_block

    # Handle list vs single object return from offset2D
    if isinstance(offset_wires_obj, list):
        offset_wires = offset_wires_obj
    else:
        offset_wires = [offset_wires_obj]
    
    # 3. Create Inner Volume (The Void)
    # FIX: We add wires to a Workplane and then extrude using the Workplane API
    inner_volume_wp = cq.Workplane("XY")
    for w in offset_wires:
        inner_volume_wp = inner_volume_wp.add(w)
        
    # Extrude the inner volume
    inner_volume_solid = inner_volume_wp.toPending().extrude(H)
    
    # 4. Create the Frame (Walls Only)
    # Subtract inner volume from full block -> Leaves a tube/frame
    frame_solid = full_block.cut(inner_volume_solid)

    print("[INFO] Step 3: Generating Lattice Block...")
    
    # Lattice Parameters
    cell_size = p["unit_cell_size"]
    strut_r = p["strut_radius"]
    
    # Calculate grid size (slightly larger than specimen)
    nx = int(L_total / cell_size) + 4
    ny = int(W_grip / cell_size) + 4
    nz = int(math.ceil(H / cell_size)) # Ensure Z covers thickness
    
    # Generate Raw Lattice Compound
    raw_lattice = create_bcc_lattice_block(cell_size, strut_r, nx, ny, nz)
    
    print("[INFO] Step 4: Cutting Lattice to fit...")
    
    # 5. Trim Lattice
    # We intersect the huge lattice block with the Inner Volume.
    # This keeps lattice only where the hole is.
    # Note: intersect works between Compound and Solid.
    try:
        # Convert Workplane object to shape for intersection
        inner_shape = inner_volume_solid.val()
        fitted_lattice = raw_lattice.intersect(inner_shape)
    except Exception as e:
        print(f"[WARNING] Lattice intersection failed: {e}")
        return frame_solid # Return frame only if lattice fails
    
    # 6. Final Union
    final_part = frame_solid.union(fitted_lattice)
    
    return final_part

# ==============================================================================
# 4. EXPORT
# ==============================================================================
try:
    final_model = generate_open_lattice_specimen(params)

    if 'show_object' in globals():
        show_object(final_model, name="ISO_527_SLA_Lattice")

    output_folder = r"C:\Users\taner\Downloads"
    if os.path.exists(output_folder):
        stl_path = os.path.join(output_folder, "ISO_527_SLA_Lattice.stl")
        
        # High quality export for SLA printing
        cq.exporters.export(final_model, stl_path, tolerance=0.01, angularTolerance=0.1)
        print("-" * 50)
        print(f"[SUCCESS] STL Exported: {stl_path}")
        print("Note: Top and Bottom skins are OPEN for resin drainage.")
        print("-" * 50)

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"[CRITICAL ERROR] {e}")