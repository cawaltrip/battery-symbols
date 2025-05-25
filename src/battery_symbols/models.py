from math import sqrt

from svg import (
    SVG,
    Arc,
    C,
    H,
    L,
    M,
    Path,
    Rect,
    V,
    ViewBoxSpec,
    Z,
    c,
    h,
    l,
    m,
    v,
    PathData,
)


def _define_bounding_box(  # noqa: C901
    coordinates: list[PathData],
) -> tuple[int | float, int | float, int | float, int | float]:
    """
    Compute the bounding box of the given coordinates.
    :return: tuple of (min_x, min_y, max_x, max_y)
    """
    x = y = 0.0
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for cmd in coordinates:
        if isinstance(cmd, M):
            # absolute MoveTo
            x, y = cmd.x, cmd.y  # type: ignore
        elif isinstance(cmd, m):
            # relative moveto
            x += cmd.dx  # type: ignore
            y += cmd.dy  # type: ignore
        elif isinstance(cmd, L):
            # absolute LineTo
            x, y = cmd.x, cmd.y  # type: ignore
        elif isinstance(cmd, l):
            # relative line to
            x += cmd.dx  # type: ignore
            y += cmd.dy  # type: ignore
        elif isinstance(cmd, H):
            # absolute horizontal line
            x = cmd.x  # type: ignore
        elif isinstance(cmd, h):
            # relative horizontal line
            x += cmd.dx  # type: ignore
        elif isinstance(cmd, V):
            # absolute vertical line
            y = cmd.y  # type: ignore
        elif isinstance(cmd, v):
            # relative vertical line
            y += cmd.dy  # type: ignore
        elif isinstance(cmd, C):
            # absolute cubic Bézier; .x,.y is endpoint
            x, y = cmd.x, cmd.y  # type: ignore
        elif isinstance(cmd, c):
            # relative cubic Bézier; dx,dy is endpoint offset
            x += cmd.dx  # type: ignore
            y += cmd.dy  # type: ignore
        elif isinstance(cmd, Z):
            pass
        else:
            print(f"Got type I can't process: {type(cmd)}")
            continue

        # update our min/max
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    return min_x, min_y, max_x, max_y


def _scale_path(  # noqa: C901
    coordinates: list[PathData],
    scale: int | float,
    x_offset: int | float,
    y_offset: int | float,
) -> list[PathData]:
    cmds: list[PathData] = []
    for cmd in coordinates:
        if isinstance(cmd, M):
            cmds.append(M(cmd.x * scale + x_offset, cmd.y * scale + y_offset))  # type: ignore
        elif isinstance(cmd, m):
            cmds.append(m(cmd.dx * scale, cmd.dy * scale))  # type: ignore
        elif isinstance(cmd, L):
            cmds.append(L(cmd.x * scale + x_offset, cmd.y * scale + y_offset))  # type: ignore
        elif isinstance(cmd, l):
            cmds.append(l(cmd.dx * scale, cmd.dy * scale))  # type: ignore
        elif isinstance(cmd, H):
            cmds.append(H(cmd.x * scale + x_offset))  # type: ignore
        elif isinstance(cmd, h):
            cmds.append(h(cmd.dx * scale))  # type: ignore
        elif isinstance(cmd, V):
            cmds.append(V(cmd.y * scale + x_offset))  # type: ignore
        elif isinstance(cmd, v):
            cmds.append(v(cmd.dy * scale))  # type: ignore
        elif isinstance(cmd, C):
            cmds.append(
                C(
                    cmd.x1 * scale + x_offset,  # type: ignore
                    cmd.y1 * scale + y_offset,  # type: ignore
                    cmd.x2 * scale + x_offset,  # type: ignore
                    cmd.y2 * scale + y_offset,  # type: ignore
                    cmd.x * scale + x_offset,  # type: ignore
                    cmd.y * scale + y_offset,  # type: ignore
                )
            )
        elif isinstance(cmd, c):
            cmds.append(
                c(
                    cmd.dx1 * scale,  # type: ignore
                    cmd.dy1 * scale,  # type: ignore
                    cmd.dx2 * scale,  # type: ignore
                    cmd.dy2 * scale,  # type: ignore
                    cmd.dx * scale,  # type: ignore
                    cmd.dy * scale,  # type: ignore
                )
            )
        elif isinstance(cmd, Z):
            cmds.append(Z())
        else:  # Z()
            print(f"Got type I can't process: {type(cmd)}")

    return cmds


class BatteryCase:
    """
    Represents the outer battery case with configurable width.
    Height is set to half the width, stroke-width is width/20,
    corner radius is width/8 by default.
    """

    def __init__(self, width: int | float):
        self.width = width
        self.stroke_width = width / 20
        self.height = width / 2
        self.rx = width / 8  # Or just always 15?
        self.ry = self.rx
        self.x = self.stroke_width / 2
        self.y = self.stroke_width / 2
        self.fill = "none"
        self.stroke = "black"

    def draw(self, elem_id: str = "battery-case") -> Rect:
        return Rect(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            rx=self.rx,
            ry=self.ry,
            fill=self.fill,
            stroke=self.stroke,
            stroke_width=self.stroke_width,
            id=elem_id,
        )


class Anode:
    """
    Represents the anode semicircle clipped by a vertical chord.
    """

    def __init__(self, battery_case: BatteryCase):
        gap = battery_case.stroke_width
        x_outer = battery_case.x + battery_case.width + battery_case.stroke_width / 2
        self.x_chord = x_outer + gap
        self.r = battery_case.height / 4
        delta_x = self.r / 3
        self.cx = self.x_chord - delta_x
        self.cy = (
            battery_case.y + battery_case.height + battery_case.stroke_width / 2
        ) / 2
        delta_y = sqrt(self.r**2 - delta_x**2)
        self.y1 = self.cy - delta_y
        self.y2 = self.cy + delta_y
        self.fill = battery_case.stroke

    def draw(self, elem_id: str = "anode") -> Path:
        return Path(
            d=[
                M(self.x_chord, self.y1),
                Arc(
                    rx=self.r,
                    ry=self.r,
                    angle=0,
                    large_arc=False,
                    sweep=True,
                    x=self.x_chord,
                    y=self.y2,
                ),
                Z(),
            ],
            stroke="none",
            fill=self.fill,
            id=elem_id,
        )
        # doc.path(d=path_d, fill=self.fill, stroke="none", id=elem_id)


class BatteryChargeLevel:
    """
    Represents the charge level of the battery.
    """

    def __init__(
        self, battery_case: BatteryCase, charging: bool = False, charge_level: int = 100
    ):
        self.gap = battery_case.stroke_width
        self.inset = self.gap * 2
        self.x = battery_case.x + self.inset
        self.y = battery_case.y + self.inset
        self.full_width = battery_case.width - 2 * self.inset
        self.fill_width = self.full_width * (charge_level / 100)
        self.height = battery_case.height - 2 * self.inset
        self.rx = 5
        self.ry = self.rx
        self.charge_level = charge_level
        self.charging = charging
        self.fill_color = "black"

    def draw(self, elem_id: str = "charge_level") -> Rect:
        return Rect(
            x=self.x,
            y=self.y,
            width=self.fill_width,
            height=self.height,
            rx=self.rx,
            ry=self.ry,
            fill=self.fill_color,
            stroke="none",
            id=elem_id,
        )


class LightningBolt:
    """
    Contains the LightningBolt, scaled and centered
    based on the size of the BatteryCase.
    """

    base_coordinates = [
        M(57.12, 60.58),
        l(23.51, -29.46),
        c(0.44, -0.59, 0.68, -1.16, 0.68, -1.71),
        c(0, -1.06, -0.86, -1.86, -1.96, -1.86),
        h(-14.48),
        l(7.72, -20.77),
        c(0.65, -1.84, -0.42, -3.13, -1.72, -3.13),
        c(-0.65, 0, -1.35, 0.32, -1.93, 1.05),
        l(-23.51, 29.47),
        c(-0.44, 0.59, -0.73, 1.15, -0.73, 1.70),
        c(0, 1.06, 0.90, 1.86, 1.97, 1.86),
        h(14.51),
        l(-7.72, 20.81),
        c(-0.68, 1.83, 0.39, 3.10, 1.70, 3.10),
        c(0.66, 0, 1.38, -0.32, 1.96, -1.06),
        Z(),
    ]

    def __init__(
        self,
        battery_case: BatteryCase,
        base_width: int | float,
        stroke_width: int | float = 0,
        color: str = "black",
    ):
        self.stroke_width = stroke_width
        self.fill_color = color

        # Grab dimensions from the battery case
        bc_width, bc_height = battery_case.width, battery_case.height
        bc_x, bc_y = battery_case.x, battery_case.y

        # Determine if there's a scale factor
        transform_scale = bc_width / base_width

        # If the scale is 1, we can just use the base coordinates,
        # otherwise we need to scale and center the lightning bolt
        if transform_scale != 1:
            # Determine the bounding box of the base coordinates
            min_x, min_y, max_x, max_y = _define_bounding_box(
                coordinates=self.base_coordinates
            )

            bolt_w = max_x - min_x
            bolt_h = max_y - min_y

            # Figure out scale + center-offset.
            scale = min(bc_width / bolt_w, bc_height / bolt_h)
            x_offset = bc_x + (bc_width - bolt_w * scale) / 2 - min_x * scale
            y_offset = bc_y + (bc_height - bolt_h * scale) / 2 - min_y * scale

            self.commands = _scale_path(
                coordinates=self.base_coordinates,
                scale=scale,
                x_offset=x_offset,
                y_offset=y_offset,
            )
        else:
            self.commands = self.base_coordinates

    def draw(self, elem_id: str = "lightning-bolt") -> Path:
        return Path(
            d=self.commands,
            fill=self.fill_color,
            stroke=self.fill_color,
            stroke_width=self.stroke_width,
            id=elem_id,
        )


class Battery:
    """
    Combines BatteryCase, Anode, BatteryChargeLevel, and LightningBolt
    and renders the complete battery SVG, with configurable charge state
    and level.
    """

    base_battery_case_width = 120

    def __init__(
        self,
        width: int | float = base_battery_case_width,
        charging: bool = False,
        level: int = 100,
    ):
        self.case = BatteryCase(width)
        self.anode = Anode(self.case)
        self.charging = charging
        # clamp level between 0 and 100
        self.level = max(0, min(100, level))
        self.charge_level = BatteryChargeLevel(self.case, self.charging, self.level)
        self.lightning_bolt = LightningBolt(self.case, self.base_battery_case_width)
        self.lightning_bolt_mask = LightningBolt(
            self.case, self.base_battery_case_width, 12
        )

    def build_svg(self) -> SVG:
        bc = self.case
        # Canvas dimensions
        svg_width = self.anode.x_chord + (self.anode.r - (self.anode.r / 3))
        svg_height = bc.height + bc.stroke_width
        view_box = ViewBoxSpec(min_x=0, min_y=0, width=svg_width, height=svg_height)

        elements = [self.case.draw(), self.anode.draw(), self.charge_level.draw()]
        # elements = [self.case.draw(), self.anode.draw()]
        if self.charging:
            elements.append(self.lightning_bolt_mask.draw("lightning-bolt-bc-mask"))
            elements.append(self.lightning_bolt_mask.draw("lightning-bolt-cl-mask"))
            elements.append(self.lightning_bolt.draw())

        doc = SVG(
            width=svg_width,
            height=svg_height,
            viewBox=view_box,
            id="battery",
            xmlns="http://www.w3.org/2000/svg",
            elements=elements,  # type: ignore
        )
        return doc
