import cadquery as cq
from pathlib import Path
from typing import Any

from constants import (
    duct_transition_length,
    inlet_outer_diameter,
    inlet_inner_diameter,
    outlet_outer_width,
    outlet_outer_height,
    outlet_inner_width,
    outlet_inner_height,
    num_rectangles,
    num_loft_sections,
    num_points_superellipse,
    overlap,
    flange_size,
    flange_thickness,
    mounting_hole_spacing,
    mounting_hole_diameter,
    flange_corner_radius,
)
from lay_flat_on_bottom import lay_flat_on_bottom
from transition import make_transition_duct


# --------------------------------------------------------------------------- #
#  Utility helpers                                                            #
# --------------------------------------------------------------------------- #
def so(result: cq.Workplane, name: str, options: dict[str, Any] | None = None) -> None:
    """
    Show object in the CadQuery GUI if available, otherwise print a notice.
    """
    options = options or {}
    if "show_object" in locals():
        show_object(result, name=name, options=options)
    else:
        print(f"Not displaying object '{name}' – GUI not detected.")


def bounding_box(wp: cq.Workplane) -> cq.BoundBox:
    """
    Convenience wrapper around wp.val().BoundingBox().
    """
    return wp.val().BoundingBox()


def print_bb(wp: cq.Workplane, label: str = "Bounding box") -> None:
    """
    Print a nicely formatted bounding-box report for a work-plane.
    """
    bb = bounding_box(wp)
    print(f"{label}: X={bb.xlen:.1f}, Y={bb.ylen:.1f}, Z={bb.zlen:.1f}")


# --------------------------------------------------------------------------- #
#  Geometry helpers                                                           #
# --------------------------------------------------------------------------- #


def make_flange(
    base_object: cq.Workplane,
    flange_size: float,
    flange_thickness: float,
    mounting_hole_spacing: float,
    mounting_hole_diameter: float,
    inner_diameter: float,
) -> cq.Workplane:
    """
    Creates a flange with mounting holes and a central opening.

    Args:
        base_object: The base object to attach the flange to
        flange_size: Width and height of the square flange
        flange_thickness: Thickness of the flange
        mounting_hole_spacing: Distance between mounting holes
        mounting_hole_diameter: Diameter of the mounting holes
        inner_diameter: Diameter of the central hole

    Returns:
        cq.Workplane: base_object with created flange
    """
    # Create flange
    sk = (
        cq.Sketch()
        .rect(flange_size, flange_size)  # square
        .vertices()  # grab the 4 corner vertices
        .fillet(flange_corner_radius)  # 2D fillet them
    )
    with_flange = (
        cq.Workplane(obj=base_object)
        .faces(">X")
        .workplane(centerOption="CenterOfBoundBox")
        .placeSketch(sk)
        .extrude(flange_thickness)
    )

    # Add mounting holes to the flange
    with_flange = (
        with_flange.rect(
            mounting_hole_spacing, mounting_hole_spacing, forConstruction=True
        )
        .vertices()
        .circle(mounting_hole_diameter / 2.0)
        .cutThruAll()
    )
    # Add central hole for the duct
    with_flange = (
        with_flange.faces(">X")
        .workplane(centerOption="CenterOfBoundBox")
        .hole(inner_diameter, flange_thickness)
    )

    return with_flange


def add_door_cutout(
    wp: cq.Workplane,
    floor_tol: float = 1.0,
) -> cq.Workplane:
    """
    Remove the overhanging bit that would interfere with the door.

    The algorithm:
    1)  Collect vertices that are on the “floor” (Z < floor_tol).
    2)  Take the minimal X among those vertices.
    3)  Build an oversized rectangular prism on the Y-Z plane at that X.
    4)  Perform a boolean cut and return the result.
    """
    # Locate the cutting plane
    bottom_vertices = [v for v in wp.vertices() if v.Z < floor_tol]
    min_x = min(bottom_vertices, key=lambda v: v.X).X

    # Construct a generous cutting solid
    bb = bounding_box(wp)
    cutting_plane = (
        cq.Workplane("YZ", origin=(min_x, 0, 0))
        .rect(bb.ylen * 2, bb.zlen * 2)  #  oversize rectangle
        .extrude(-bb.xlen * 2)  #  extrude through part
    )

    # Remove the part that would interfere with the door
    return wp.cut(cutting_plane)


# --------------------------------------------------------------------------- #
#  Build model                                                                #
# --------------------------------------------------------------------------- #
def build_transition_duct() -> cq.Workplane:
    """
    Compose the final model step by step and return the finished Workplane.
    """
    # Core duct body
    duct_solid = make_transition_duct(
        duct_transition_length=duct_transition_length,
        inlet_outer_diameter=inlet_outer_diameter,
        inlet_inner_diameter=inlet_inner_diameter,
        outlet_outer_width=outlet_outer_width,
        outlet_outer_height=outlet_outer_height,
        outlet_inner_width=outlet_inner_width,
        outlet_inner_height=outlet_inner_height,
        num_rectangles=num_rectangles,
        num_loft_sections=num_loft_sections,
        num_points_superellipse=num_points_superellipse,
        overlap=overlap,
    )

    # Add flange
    with_base_flange = make_flange(
        duct_solid,
        flange_size,
        flange_thickness,
        mounting_hole_spacing,
        mounting_hole_diameter,
        inlet_inner_diameter,
    )

    # Orient so that the bottom faces lie on the XY plane
    flange_flat_on_bottom = lay_flat_on_bottom(with_base_flange)

    # Remove the bit that collides with the cabinet door
    with_cutout_for_door = add_door_cutout(flange_flat_on_bottom)

    return with_cutout_for_door


# --------------------------------------------------------------------------- #
#  Main script                                                                #
# --------------------------------------------------------------------------- #

final_duct = build_transition_duct()
print_bb(final_duct, "Final part")

# Visual
so(final_duct, "Transition-Duct + Door cutout", {"color": "red", "alpha": 0.1})

# Export
output_path = Path("stl/door_fan_duct.stl")
output_path.parent.mkdir(parents=True, exist_ok=True)
cq.exporters.export(
    final_duct, str(output_path), tolerance=2e-4, angularTolerance=0.03
)  # Without these tolerances, there will be ripples near the edges of rectangularish sections.
print(f"STL written to {output_path.resolve()}")
