from math import sqrt
from svg import (
    C,
    H,
    L,
    M,
    Path,
    Q,
    V,
    Z,
    c,
    h,
    l,
    m,
    q,
    v,
    PathData,
)
from typing import Optional
import skia


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


def _mask_path(subject_path: skia.Path, clip_path: skia.Path) -> skia.Path:
    """
    Create a mask by combining two paths.
    The top path will be subtracted from the bottom path.
    """
    return skia.Op(subject_path, clip_path, skia.PathOp.kDifference_PathOp)


def _to_path(shape: skia.RRect, paint: skia.Paint) -> skia.Path:
    """
    Convert a skia.RRect object to a skia.Path object.
    """
    path = skia.Path()
    path.addRRect(object)
    return path


def _path_and_mask(
    subject_path: skia.RRect,
    subject_paint: skia.Paint,
    clip_path: Optional[skia.Path] = None,
) -> skia.Path:
    old_path = skia.Path().addRRect(subject_path)
    paint = skia.Paint(subject_paint)
    new_path = skia.Path()
    paint.getFillPath(old_path, new_path)
    if clip_path is not None:
        new_path = skia.Op(new_path, clip_path, skia.PathOp.kDifference_PathOp)
    return new_path


class BatteryCase:
    """
    Represents the outer battery case with configurable width.
    Height is set to half the width, stroke-width is width/20,
    corner radius is width/8 by default.
    """

    def __init__(self, width: float, radius: float = 15, elem_id: str = "battery-case"):
        self.width = width
        self.stroke_width = width / 20
        self.height = width / 2
        self.rx = radius
        self.ry = self.rx
        self.x = self.stroke_width / 2
        self.y = self.stroke_width / 2
        self.id = elem_id

        self._rectangle = skia.Rect(
            self.x, self.y, (self.x + self.width), (self.y + self.height)
        )
        self._rounded_rectangle = skia.RRect(self._rectangle, self.rx, self.ry)
        self.shape = self._rounded_rectangle
        # self.shape = skia.Path().addRRect(skia.RRect(self.rectangle, self.rx, self.ry))
        self.paint = skia.Paint(
            Style=skia.Paint.kStroke_Style, StrokeWidth=self.stroke_width
        )

    def path_and_mask(self, mask_path: Optional[skia.Path] = None) -> None:
        """
        Create a path and apply a mask if provided.
        """
        self.shape = _path_and_mask(self.shape, self.paint, mask_path)
        self.paint.setStyle(skia.Paint.kFill_Style)


class BatteryChargeLevel:
    """
    Represents the charge level of the battery.
    """

    # TODO: Make sure the height of this is correct.  Might need to be doubled.
    def __init__(
        self,
        battery_case: BatteryCase,
        charging: bool = False,
        charge_level: int = 100,
        elem_id: str = "charge-level",
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
        self.id = elem_id

        self._rectangle = skia.Rect(
            self.x, self.y, (self.x + self.fill_width), (self.y + self.height)
        )
        self._rounded_rectangle = skia.RRect(self._rectangle, self.rx, self.ry)
        self.shape = self._rounded_rectangle
        # self.shape = skia.Path().addRRect(skia.RRect(self._rectangle, self.rx, self.ry))
        self.paint = skia.Paint(Style=skia.Paint.kFill_Style)

    def path_and_mask(self, mask_path: Optional[skia.Path] = None) -> None:
        """
        Create a path and apply a mask if provided.
        """
        self.shape = _path_and_mask(self.shape, self.paint, mask_path)


class Anode:
    """
    Represents the anode semicircle clipped by a vertical chord.
    """

    def __init__(self, battery_case: BatteryCase, elem_id: str = "anode"):
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
        self.id = elem_id

        # Create the Skia Path for the anode shape
        path = skia.Path()
        path.moveTo(self.x_chord, self.y1)
        path.arcTo(
            rx=self.r,
            ry=self.r,
            xAxisRotate=0,
            largeArc=skia.Path.kSmall_ArcSize,
            sweep=skia.PathDirection.kCW,
            x=self.x_chord,
            y=self.y2,
        )
        path.close()

        self.shape = path
        self.paint = skia.Paint(
            Style=skia.Paint.kFill_Style, Color=skia.ColorBLACK
        )  # Replace with actual color eventually? If needed?


class LightningBolt:
    """Contains the LightningBolt, scaled and centered"""

    base_coordinates = [
        M(57.12, 60.58),
        l(23.51, -29.46),
        q(0.67, -0.89, 0.68, -1.71),
        q(-0.16, -1.72, -1.96, -1.86),
        h(-14.48),
        l(7.72, -20.77),
        q(0.60, -2.94, -1.72, -3.13),
        q(-1.02, -0.02, -1.93, 1.05),
        l(-23.51, 29.47),
        q(-0.69, 0.88, -0.73, 1.70),
        q(0.18, 1.73, 1.97, 1.86),
        h(14.51),
        l(-7.72, 20.81),
        q(-0.64, 2.92, 1.70, 3.10),
        q(1.04, 0.02, 1.96, -1.06),
        Z(),
    ]

    def __init__(  # noqa: C901
        self,
        battery_case: BatteryCase,
        base_width: float,
        stroke_width: float = 0,
        elem_id: str = "lightning-bolt",
    ):
        self.stroke_width = stroke_width
        self.id = elem_id
        # if stroke_width > 0:
        #     self.paint = skia.Paint(Style=skia.Paint.kStrokeAndFill_Style, Color=skia.ColorBLACK, StrokeWidth=self.stroke_width)
        # else:
        #     self.paint = skia.Paint(Style=skia.Paint.kFill_Style, Color=skia.ColorBLACK)
        self.paint = skia.Paint(Style=skia.Paint.kFill_Style, Color=skia.ColorBLACK)

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

            commands = _scale_path(
                coordinates=self.base_coordinates,
                scale=scale,
                x_offset=x_offset,
                y_offset=y_offset,
            )
        else:
            commands = self.base_coordinates

        # Now that the coordinates are scaled and centered, let's create the Skia Path
        # This could probably be done with `Path.Make`, but until I understand skia better,
        # I'll manually create the path using the commands.
        # TODO: Figure out if the C and Q commands work properly.
        self.shape = skia.Path()
        previous_command: dict[str, float] = {}
        for cmd in commands:
            if isinstance(cmd, M):
                self.shape.moveTo(cmd.x, cmd.y)
            elif isinstance(cmd, m):
                self.shape.rMoveTo(cmd.dx, cmd.dy)
            elif isinstance(cmd, L):
                self.shape.lineTo(cmd.x, cmd.y)
            elif isinstance(cmd, l):
                self.shape.rLineTo(cmd.dx, cmd.dy)
            elif isinstance(cmd, H):
                self.shape.lineTo(cmd.x, previous_command.get("y", 0))
            elif isinstance(cmd, h):
                # self.shape.lineTo(previous_command.get("x", 0) + cmd.dx, previous_command.get("y", 0))
                self.shape.rLineTo(cmd.dx, 0)
            elif isinstance(cmd, V):
                self.shape.lineTo(previous_command.get("x", 0), cmd.y)
            elif isinstance(cmd, v):
                self.shape.rLineTo(0, cmd.dy)
            elif isinstance(cmd, C):
                self.shape.cubicTo(cmd.x1, cmd.y1, cmd.x2, cmd.y2, cmd.x, cmd.y)
            elif isinstance(cmd, c):
                self.shape.rCubicTo(cmd.dx1, cmd.dy1, cmd.dx2, cmd.dy2, cmd.dx, cmd.dy)
            elif isinstance(cmd, Q):
                self.shape.quadTo(cmd.x1, cmd.y1, cmd.x, cmd.y)
            elif isinstance(cmd, q):
                self.shape.rQuadTo(cmd.dx1, cmd.dy1, cmd.dx, cmd.dy)
            elif isinstance(cmd, Z):
                pass  # We'll close the shape regardless at the end.
            else:
                print(f"Unknown command: {cmd}")

            previous_command = {}
            if hasattr(cmd, "x"):
                previous_command["x"] = cmd.x
            elif hasattr(cmd, "dx"):
                previous_command["x"] = cmd.dx
            if hasattr(cmd, "y"):
                previous_command["y"] = cmd.y
            elif hasattr(cmd, "dy"):
                previous_command["y"] = cmd.dy

        self.shape.close()

        if self.stroke_width > 0:
            paint = skia.Paint(
                Style=skia.Paint.kStrokeAndFill_Style,
                StrokeWidth=self.stroke_width,
                StrokeJoin=skia.Paint.kMiter_Join,
                StrokeCap=skia.Paint.kButt_Cap,
            )
            outline = skia.Path()
            paint.getFillPath(self.shape, outline)
            self.shape = outline


class Battery:
    """
    Combines BatteryCase, Anode, BatteryChargeLevel, and LightningBolt
    and renders the complete battery SVG, with configurable charge state
    and level.
    """

    base_battery_case_width = 120

    def __init__(  # noqa: C901
        self,
        width: float = base_battery_case_width,
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
            self.case, self.base_battery_case_width, 12, elem_id="lightning-bolt-mask"
        )

        mask = self.lightning_bolt_mask.shape if self.charging else None
        self.case.path_and_mask(mask)
        self.charge_level.path_and_mask(mask)

        # Keeping this in case it's needed later, but I don't think it's strictly necessary for what we're doing here.
        self.elements: list[
            BatteryCase | Anode | BatteryChargeLevel | LightningBolt
        ] = [self.case, self.anode, self.charge_level]
        if self.charging:
            self.elements.append(self.lightning_bolt)
            self.elements.append(self.lightning_bolt_mask)

    def build_svg(self, output_file: Path) -> None:
        # Canvas dimensions
        svg_width = self.anode.x_chord + (self.anode.r - (self.anode.r / 3))
        svg_height = self.case.height + self.case.stroke_width

        stream = skia.FILEWStream(str(output_file))
        canvas = skia.SVGCanvas.Make(bounds=(svg_width, svg_height), stream=stream)  # type: ignore[call-arg]

        # Battery case
        canvas.drawPath(self.case.shape, self.case.paint)

        # Anode
        canvas.drawPath(self.anode.shape, self.anode.paint)

        # Charge level
        if self.level > 0:
            canvas.drawPath(self.charge_level.shape, self.charge_level.paint)

        # Lightning bolt
        if self.charging:
            canvas.drawPath(self.lightning_bolt.shape, self.lightning_bolt.paint)

        del canvas
        stream.flush()
