from math import pi, sin, cos, copysign, gamma, sqrt
import cadquery as cq


# Geometry helpers
def _superellipse_point(t: float, a: float, b: float, n: float) -> tuple[float, float]:
    """
    Calculates a point (x, y) on a superellipse for a given angle t (radians).

    Args:
        t (float): Angle in radians (0 to 2*pi).
        a (float): Semi-axis length along the x-axis.
        b (float): Semi-axis length along the y-axis.
        n (float): Exponent controlling the shape (n=2 is ellipse, n->inf is rectangle).

    Returns:
        tuple: (x, y) coordinates of the point on the superellipse.
    """
    cos_t: float = cos(t)
    sin_t: float = sin(t)
    # Parametric form: x = a*sign(cos t)*|cos t|^(2/n), y = b*sign(sin t)*|sin t|^(2/n)
    term_x: float = copysign(abs(cos_t) ** (2.0 / n), cos_t) if cos_t != 0 else 0.0
    term_y: float = copysign(abs(sin_t) ** (2.0 / n), sin_t) if sin_t != 0 else 0.0
    return (a * term_x, b * term_y)


def _build_profile(
    a: float, b: float, n: float, num_points: int
) -> list[tuple[float, float]]:
    """
    Build a closed polyline approximating a super-ellipse.

    Args:
        a: Semi-axis along Y.
        b: Semi-axis along Z.
        n: Super-ellipse exponent.
        num_points: Number of points to use for the polyline.

    Returns:
        List of (y, z) tuples for Workplane.polyline().
    """
    step: float = 2 * pi / num_points
    return [_superellipse_point(step * i, a, b, n) for i in range(num_points)]


def _superellipse_area(a: float, b: float, n: float) -> float:
    """
    Closed-form area of a super-ellipse.

    A = 4ab * Γ(1 + 1/n)^2 / Γ(1 + 2/n)

    Args:
        a, b: Semi-axes.
        n: Exponent.

    Returns:
        Cross-sectional area.
    """
    k: float = 4.0 * gamma(1.0 + 1.0 / n) ** 2 / gamma(1.0 + 2.0 / n)
    return k * a * b


# Loft builder
def _loft_between_ends(
    length: float,
    a_in: float,
    b_in: float,
    n_in: float,
    a_out: float,
    b_out: float,
    n_out_local: float,
    num_loft_sections: int,
    num_points: int,
    offset_start: float = 0.0,
    offset_end: float = 0.0,
) -> cq.Solid:
    """
    Create a solid by lofting between two super-ellipse cross-sections.

    The loft grows along +X, with X = 0 at the rectangular outlet and
    X = `length` at the round inlet.

    Args:
        length: Total nominal length of the loft.
        a_in, b_in, n_in: Super-ellipse parameters at the **inlet** (round).
        a_out, b_out, n_out_local: Parameters at the **outlet** (rectangular).
        num_loft_sections: Number of intermediate sections for lofting.
        num_points: Points per cross-section polyline.
        offset_start: Trim applied to first (outlet) section.
        offset_end:   Trim applied to last (inlet) section.

    Returns:
        CadQuery Solid representing the loft.
    """
    # Effective length after trimming both ends
    effective_len: float = length - (offset_start + offset_end)

    # Pre-compute X positions of all the work-planes
    x_positions: list[float] = [
        offset_start + effective_len * (i / num_loft_sections)
        for i in range(num_loft_sections + 1)
    ]

    # Pre-compute inlet/outlet areas
    area_in: float = _superellipse_area(a_in, b_in, n_in)
    area_out: float = _superellipse_area(a_out, b_out, n_out_local)

    wp: cq.Workplane = cq.Workplane("YZ")  # Normal points along +X
    previous_x: float | None = None

    for i, x in enumerate(x_positions):
        s: float = i / num_loft_sections  # 0 → outlet, 1 → inlet

        # Target cross-sectional area (linear taper)
        area_target: float = area_out + (area_in - area_out) * s

        # Linear interpolation gives a *shape* guess (aspect ratio)
        a0: float = a_out + (a_in - a_out) * s
        b0: float = b_out + (b_in - b_out) * s
        n: float = n_out_local + (n_in - n_out_local) * s

        # Scale a0, b0 uniformly so that area matches area_target
        area_guess: float = _superellipse_area(a0, b0, n)
        scale: float = sqrt(area_target / area_guess) if area_guess != 0 else 1.0
        a: float = a0 * scale
        b: float = b0 * scale

        profile: list[tuple[float, float]] = _build_profile(a, b, n, num_points)

        if previous_x is None:
            # First section drawn on the base work-plane
            wp = wp.polyline(profile).close()
        else:
            # Offset a new work-plane along X and draw the next wire
            wp = wp.workplane(offset=x - previous_x).polyline(profile).close()

        previous_x = x

    # A single loft call stitches all wires into a solid
    return wp.loft(combine=True, ruled=False).val()


def make_transition_duct(
    duct_transition_length: float,
    inlet_outer_diameter: float,
    inlet_inner_diameter: float,
    outlet_outer_width: float,
    outlet_outer_height: float,
    outlet_inner_width: float,
    outlet_inner_height: float,
    num_rectangles: float,
    num_loft_sections: int,
    num_points_superellipse: int,
    overlap: float,
) -> cq.Solid:
    """
    Build the complete hollow transition duct.

    Args:
        duct_transition_length: Length of the transition duct.
        inlet_outer_diameter: Outer diameter of the inlet (round end).
        inlet_inner_diameter: Inner diameter of the inlet (round end).
        outlet_outer_width: Outer width of the outlet (rectangular end).
        outlet_outer_height: Outer height of the outlet (rectangular end).
        outlet_inner_width: Inner width of the outlet (rectangular end).
        outlet_inner_height: Inner height of the outlet (rectangular end).
        num_rectangles: Superellipse exponent for rectangular end.
        num_loft_sections: Number of sections for lofting.
        num_points_superellipse: Number of points to use for each cross-section.
        overlap: Overlap amount for the inner shell.

    Returns:
        CadQuery Solid with wall_thickness walls.
    """
    # Outside shell
    outer_solid: cq.Solid = _loft_between_ends(
        length=duct_transition_length,
        # Inlet (round, outer dimensions)
        a_in=inlet_outer_diameter / 2,
        b_in=inlet_outer_diameter / 2,
        n_in=2.0,  # Perfect circle
        # Outlet (rectangularish, outer dimensions)
        a_out=outlet_outer_width / 2,
        b_out=outlet_outer_height / 2,
        n_out_local=num_rectangles,
        num_loft_sections=num_loft_sections,
        num_points=num_points_superellipse,
    )

    # Inside shell
    inner_solid: cq.Solid = _loft_between_ends(
        length=duct_transition_length + overlap,
        # Inlet (round, inner)
        a_in=inlet_inner_diameter / 2,
        b_in=inlet_inner_diameter / 2,
        n_in=2.0,
        # Outlet (rectangularish, inner)
        a_out=outlet_inner_width / 2,
        b_out=outlet_inner_height / 2,
        n_out_local=num_rectangles,
        num_loft_sections=num_loft_sections,
        num_points=num_points_superellipse,
        # Recessed slightly to guarantee a clean Boolean
        offset_start=overlap,
        offset_end=overlap,
    )

    # Hollow part
    duct_solid: cq.Solid = outer_solid.cut(inner_solid)
    # Select the inlet face (normal roughly pointing ±X) and cut a hole
    part_with_hole: cq.Solid = (
        cq.Workplane(obj=duct_solid)
        .faces(">X")  # faces whose normal ≈ +X
        .workplane(centerOption="CenterOfMass")  # place WP on that face
        .circle((inlet_inner_diameter - overlap) / 2)  # inner diameter
        .cutBlind(-overlap)  # cut *into* the part
        .val()
    )

    return part_with_hole
