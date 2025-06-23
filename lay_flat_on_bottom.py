import math
import cadquery as cq


def lay_flat_on_bottom(solid: cq.Workplane | cq.Solid | cq.Compound) -> cq.Workplane:
    """
    Rotate a transition duct so that its outside bottom wall is parallel to the
    XY–plane and rests on Z = 0.

    Parameters
    ----------
    solid : cq.Workplane | cq.Solid | cq.Compound
        The solid returned by `make_transition_duct`.

    Returns
    -------
    cq.Workplane
        A Workplane that contains the correctly oriented solid.
    """

    # Make sure we have a Workplane to work with
    wp = cq.Workplane(obj=solid) if isinstance(solid, cq.Solid) else solid

    # ------------------------------------------------------------------
    # 1. Pick the two end faces   (normals ≃ −X   and   +X)
    # ------------------------------------------------------------------
    face_rect = wp.faces("<X").val()  # rectangular (outlet) end
    face_circ = wp.faces(">X").val()  # circular    (inlet)  end

    bb_rect = face_rect.BoundingBox()
    bb_circ = face_circ.BoundingBox()

    # Lowest Z on both ends and the X–distance between them
    z_rect = bb_rect.zmin
    z_circ = bb_circ.zmin
    x_rect = bb_rect.xmin  # any X from that face will do – it is planar
    x_circ = bb_circ.xmax
    length = x_circ - x_rect

    # ------------------------------------------------------------------
    # 2. Angle that makes the bottom horizontal
    # ------------------------------------------------------------------
    slope = (z_circ - z_rect) / length  # ΔZ / ΔX
    angle_deg = math.degrees(math.atan(slope))  # plus → pitch down

    # ------------------------------------------------------------------
    # 3. Rotate about global Y
    # ------------------------------------------------------------------
    flat = wp.rotate((0, 0, 0), (0, 1, 0), angle_deg)

    # ------------------------------------------------------------------
    # 4. Translate so that z-min becomes 0
    # ------------------------------------------------------------------
    zmin_after = flat.val().BoundingBox().zmin
    flat = flat.translate((0, 0, -zmin_after))

    return flat
