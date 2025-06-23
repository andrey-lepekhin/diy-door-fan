# Parameters (user configuration)

inlet_inner_diameter: float = (
    125.0  # mm, Input diameter (inner diameter of duct at start)
)
wall_thickness: float = 1.6  # mm, Thickness of the duct walls
duct_transition_length: float = 170.0  # mm, Length of the duct transition (X-axis)

outlet_outer_height: float = 20.0  # mm, Target outer height of the rectangle
outlet_outer_width: float = 233.0  # mm, Target outer width of the rectangle

outlet_inner_height: float = (
    outlet_outer_height - 2 * wall_thickness
)  # mm, Target inner height of the rectangle

outlet_inner_width: float = (
    outlet_outer_width - 2 * wall_thickness
)  # mm, Target inner width of the rectangle

inlet_outer_diameter: float = inlet_inner_diameter + (2 * wall_thickness)

# Define a small overlap distance to ensure boolean operations (union/cut) work reliably
overlap: float = 0.01  # mm

# Lofting parameters
num_loft_sections: int = 40  # Number of intermediate sections for loft smoothness (adjust for quality vs computation)
num_rectangles: float = 10.0  # Superellipse exponent for rectangle approximation (higher => sharper corners)
num_points_superellipse: int = (
    128  # Number of points per profile section wire for better resolution
)


# Fan flange
flange_thickness: float = 1.8  # mm, Thickness of the mounting flange
# Flange outer size derived from input diameter + margin
flange_size: float = (
    inlet_inner_diameter + 2 * wall_thickness
)  # mm, Overall side length of the square flange
mounting_hole_spacing: float = 105.0  # mm, Center-to-center distance for mounting holes
mounting_hole_diameter: float = (
    4.3  # mm, Diameter for mounting holes (e.g., for M4 screws)
)
flange_corner_radius: float = flange_size * 0.1  # mm, Corner radius for the flange
