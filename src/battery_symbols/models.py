from abc import ABC, abstractmethod
from math import sqrt
from typing import Optional

import skia
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

from battery_symbols.config import FONTS_DIR


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
        elif isinstance(cmd, Q):
            # absolute quadratic Bézier; .x,.y is endpoint
            x, y = cmd.x, cmd.y
        elif isinstance(cmd, q):
            # relative quadratic Bézier; dx,dy is endpoint offset
            x += cmd.dx
            y += cmd.dy
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
    scale_x: float,
    scale_y: float,
    x_offset: float,
    y_offset: float,
) -> list[PathData]:
    cmds: list[PathData] = []
    for cmd in coordinates:
        if isinstance(cmd, M):
            cmds.append(M(cmd.x * scale_x + x_offset, cmd.y * scale_y + y_offset))  # type: ignore
        elif isinstance(cmd, m):
            cmds.append(m(cmd.dx * scale_x, cmd.dy * scale_y))  # type: ignore
        elif isinstance(cmd, L):
            cmds.append(L(cmd.x * scale_x + x_offset, cmd.y * scale_y + y_offset))  # type: ignore
        elif isinstance(cmd, l):
            cmds.append(l(cmd.dx * scale_x, cmd.dy * scale_y))  # type: ignore
        elif isinstance(cmd, H):
            cmds.append(H(cmd.x * scale_x + x_offset))  # type: ignore
        elif isinstance(cmd, h):
            cmds.append(h(cmd.dx * scale_x))  # type: ignore
        elif isinstance(cmd, V):
            cmds.append(V(cmd.y * scale_y + y_offset))  # type: ignore
        elif isinstance(cmd, v):
            cmds.append(v(cmd.dy * scale_y))  # type: ignore
        elif isinstance(cmd, C):
            cmds.append(
                C(
                    cmd.x1 * scale_x + x_offset,  # type: ignore
                    cmd.y1 * scale_y + y_offset,  # type: ignore
                    cmd.x2 * scale_x + x_offset,  # type: ignore
                    cmd.y2 * scale_y + y_offset,  # type: ignore
                    cmd.x * scale_x + x_offset,  # type: ignore
                    cmd.y * scale_y + y_offset,  # type: ignore
                )
            )
        elif isinstance(cmd, c):
            cmds.append(
                c(
                    cmd.dx1 * scale_x,  # type: ignore
                    cmd.dy1 * scale_y,  # type: ignore
                    cmd.dx2 * scale_x,  # type: ignore
                    cmd.dy2 * scale_y,  # type: ignore
                    cmd.dx * scale_x,  # type: ignore
                    cmd.dy * scale_y,  # type: ignore
                )
            )
        elif isinstance(cmd, Q):
            cmds.append(
                Q(
                    cmd.x1 * scale_x + x_offset,  # type: ignore
                    cmd.y1 * scale_y + y_offset,  # type: ignore
                    cmd.x * scale_x + x_offset,  # type: ignore
                    cmd.y * scale_y + y_offset,  # type: ignore
                )
            )
        elif isinstance(cmd, q):
            cmds.append(
                q(
                    cmd.dx1 * scale_x,  # type: ignore
                    cmd.dy1 * scale_y,  # type: ignore
                    cmd.dx * scale_x,  # type: ignore
                    cmd.dy * scale_y,  # type: ignore
                )
            )
        elif isinstance(cmd, Z):
            cmds.append(Z())
        else:  # Z()
            print(f"_scale_path_percentage: Got type I can't process: {type(cmd)}")

    return cmds


def _path_and_mask(
    subject_path: skia.RRect,
    subject_paint: skia.Paint,
    clip_path: Optional[skia.Path] = None,
) -> skia.Path:
    if isinstance(subject_path, skia.RRect):
        old_path = skia.Path().addRRect(subject_path)
    elif isinstance(subject_path, skia.Path):
        # old_path = skia.Path().addPath(subject_path)
        old_path = subject_path
    else:
        raise TypeError("subject_path must be skia.RRect or skia.Path")

    if isinstance(clip_path, skia.RRect):
        clip_path = skia.Path().addRRect(clip_path)
    elif not isinstance(clip_path, skia.Path) and clip_path is not None:
        raise TypeError("clip_path must be skia.RRect or skia.Path or None")

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
    """Contains the lightning bolt, scaled and centered"""

    ORIGINAL_WIDTH = 120.0
    ORIGINAL_HEIGHT = 60.0

    original_coordinates = [
        l((23.51 / ORIGINAL_WIDTH), (-29.46 / ORIGINAL_HEIGHT)),
        q(
            (0.67 / ORIGINAL_WIDTH),
            (-0.89 / ORIGINAL_HEIGHT),
            (0.68 / ORIGINAL_WIDTH),
            (-1.71 / ORIGINAL_HEIGHT),
        ),
        q(
            (-0.16 / ORIGINAL_WIDTH),
            (-1.72 / ORIGINAL_HEIGHT),
            (-1.96 / ORIGINAL_WIDTH),
            (-1.86 / ORIGINAL_HEIGHT),
        ),
        h((-14.48 / ORIGINAL_WIDTH)),
        l((7.72 / ORIGINAL_WIDTH), (-20.77 / ORIGINAL_HEIGHT)),
        q(
            (0.6 / ORIGINAL_WIDTH),
            (-2.94 / ORIGINAL_HEIGHT),
            (-1.72 / ORIGINAL_WIDTH),
            (-3.13 / ORIGINAL_HEIGHT),
        ),
        q(
            (-1.02 / ORIGINAL_WIDTH),
            (-0.02 / ORIGINAL_HEIGHT),
            (-1.93 / ORIGINAL_WIDTH),
            (1.05 / ORIGINAL_HEIGHT),
        ),
        l((-23.51 / ORIGINAL_WIDTH), (29.47 / ORIGINAL_HEIGHT)),
        q(
            (-0.69 / ORIGINAL_WIDTH),
            (0.88 / ORIGINAL_HEIGHT),
            (-0.73 / ORIGINAL_WIDTH),
            (1.7 / ORIGINAL_HEIGHT),
        ),
        q(
            (0.18 / ORIGINAL_WIDTH),
            (1.73 / ORIGINAL_HEIGHT),
            (1.97 / ORIGINAL_WIDTH),
            (1.86 / ORIGINAL_HEIGHT),
        ),
        h((14.51 / ORIGINAL_WIDTH)),
        l((-7.72 / ORIGINAL_WIDTH), (20.81 / ORIGINAL_HEIGHT)),
        q(
            (-0.64 / ORIGINAL_WIDTH),
            (2.92 / ORIGINAL_HEIGHT),
            (1.7 / ORIGINAL_WIDTH),
            (3.1 / ORIGINAL_HEIGHT),
        ),
        q(
            (1.04 / ORIGINAL_WIDTH),
            (0.02 / ORIGINAL_HEIGHT),
            (1.96 / ORIGINAL_WIDTH),
            (-1.06 / ORIGINAL_HEIGHT),
        ),
        Z(),
    ]

    def __init__(  # noqa: C901
        self,
        base_x: float,
        base_y: float,
        base_width: float,
        base_height: float,
        x_offset_percentage: float,
        y_offset_percentage: float,
        total_scale: float = 1.0,
        stroke_width: float = 0.0,
    ):
        # Set the easy things
        self.stroke_width = (
            stroke_width * (base_width / self.ORIGINAL_WIDTH)
            if stroke_width > 0
            else 0.0
        )
        self.paint = skia.Paint(Style=skia.Paint.kFill_Style)
        scale_x = base_width * total_scale
        scale_y = base_height * total_scale

        # Determine initial coordinates
        x = base_x + (base_width * x_offset_percentage)
        y = base_y + (base_height * y_offset_percentage)

        commands = _scale_path(
            coordinates=self.original_coordinates,
            scale_x=scale_x,
            scale_y=scale_y,
            x_offset=x,
            y_offset=y,
        )

        commands.insert(0, M(x, y))  # Start at the offset position

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


class Number:
    """
    Represents a number in the battery SVG.
    This is a placeholder for future use, as the current implementation does not
    include text rendering.
    """

    def __init__(
        self,
        base_x: float,
        base_y: float,
        base_width: float,
        base_height: float,
        x_offset_pct: float,
        font_path: Path,
        level: int,
        total_scale: float = 1.0,
        fill_color: int = skia.ColorBLACK,
    ):
        self.paint = skia.Paint(Style=skia.Paint.kFill_Style, Color=fill_color)
        text = str(max(0, min(100, level)))
        # Load typeface and set font size based on battery height
        typeface = skia.Typeface.MakeFromFile(str(font_path))
        if not typeface:
            raise RuntimeError("Couldn't load font")
        # font_size = base_height * total_scale * 0.6
        font_size = base_height * 0.6
        font = skia.Font(typeface, font_size)

        metrics = font.getMetrics()
        center_offset = (metrics.fAscent + metrics.fDescent) / 2.0
        y_offset_pct = (base_height / 2.0 - center_offset) / base_height

        # Convert text → glyph IDs
        glyph_ids = font.textToGlyphs(text, encoding=skia.TextEncoding.kUTF8)

        # Compute starting pen position
        x = base_x + base_width * x_offset_pct
        y = base_y + base_height * y_offset_pct

        rx = 6
        ry = rx

        # Build a single path by translating each glyph outline
        path = skia.Path()
        cursor = x
        for gid in glyph_ids:
            glyph_path = font.getPath(gid)
            if glyph_path:
                matrix = skia.Matrix.Translate(cursor, y)
                path.addPath(glyph_path, matrix)
            advance = font.getWidths([gid])[0]
            cursor += advance

        self.shape = path

        bounding_box_rect = self.shape.computeTightBounds()

        x_diff = abs(bounding_box_rect.right() - bounding_box_rect.left()) * 0.1
        y_diff = abs(bounding_box_rect.bottom() - bounding_box_rect.top()) * 0.1

        bounding_box_rect = skia.Rect(
            (bounding_box_rect.left() - (x_diff / 2) - (rx / 2)),
            (bounding_box_rect.top() - (y_diff / 2) - (ry / 2)),
            (bounding_box_rect.right() + (x_diff / 2) + (rx / 2)),
            (bounding_box_rect.bottom() + (y_diff / 2) + (ry / 2)),
        )

        self.bounding_box = skia.RRect(bounding_box_rect, rx, ry)
        # TODO: Figure out masking.
        # self.path_and_mask(mask_path=self.bounding_box)

    def path_and_mask(self, mask_path: Optional[skia.Path] = None) -> None:
        """
        Create a path and apply a mask if provided.
        """

        # self.shape = _path_and_mask(self.shape, self.paint, mask_path)
        self.shape = _path_and_mask(mask_path, self.paint, self.shape)


class Battery(ABC):
    """
    Base class for battery symbols.
    This class is not intended to be instantiated directly.
    It serves as a base for other battery classes.
    """

    BASE_CASE_WIDTH = 120.0

    def __init__(self, width: float, charging: bool, level: int, **kwargs: Path):
        self.width = width
        self.charging = charging
        # Clamp level between 0 and 100
        self.level = max(0, min(100, level))
        self.elements: list[tuple[skia.Path, skia.Paint]] = []
        self.svg_width = 0.0
        self.svg_height = 0.0
        self.transform_scale = (
            1.0
            if self.width == self.BASE_CASE_WIDTH
            else self.width / self.BASE_CASE_WIDTH
        )
        self._assemble()

    @abstractmethod
    def _assemble(self) -> None:
        """
        Assemble the battery components.
        This method should be overridden by subclasses to define the specific battery components.
        """
        raise NotImplementedError("Subclasses must implement _assemble method.")

    def build_svg(self, output_file: Path) -> None:
        stream = skia.FILEWStream(str(output_file))
        canvas = skia.SVGCanvas.Make(
            bounds=(self.svg_width, self.svg_height), stream=stream
        )  # type: ignore[call-arg]
        # print(f"svg_width: {self.svg_width}, svg_height: {self.svg_height}")

        for shape, paint in self.elements:
            # print(f"Drawing shape: {shape}, with paint: {paint}")
            # Draw each shape with its corresponding paint
            if isinstance(shape, skia.Path):
                canvas.drawPath(shape, paint)
            elif isinstance(shape, skia.RRect):
                canvas.drawRRect(shape, paint)
            elif isinstance(shape, skia.Rect):
                canvas.drawRect(shape, paint)

        del canvas
        stream.flush()


class SimpleBattery(Battery):
    """
    Combines BatteryCase, Anode, BatteryChargeLevel, and LightningBolt
    and renders the complete battery SVG, with configurable charge state
    and level.
    """

    def __init__(
        self,
        width: float = Battery.BASE_CASE_WIDTH,
        charging: bool = False,
        level: int = 100,
        **kwargs: Path,
    ):
        super().__init__(width, charging, level)

    def _assemble(self) -> None:
        """
        Assemble the battery components.
        This method defines the specific battery components for the SimpleBattery.
        """
        self.case = BatteryCase(self.width)
        self.anode = Anode(self.case)
        self.charge_level = BatteryChargeLevel(self.case, self.charging, self.level)

        # Determine lightning bolt offsets:
        bolt_x_offset_percentage = 0.45
        bolt_y_offset_percentage = 0.96

        self.lightning_bolt = LightningBolt(
            self.case.x,
            self.case.y,
            self.case.width,
            self.case.height,
            bolt_x_offset_percentage,
            bolt_y_offset_percentage,
        )
        self.lightning_bolt_mask = LightningBolt(
            self.case.x,
            self.case.y,
            self.case.width,
            self.case.height,
            bolt_x_offset_percentage,
            bolt_y_offset_percentage,
            stroke_width=12,
        )

        mask = self.lightning_bolt_mask.shape if self.charging else None
        self.case.path_and_mask(mask)
        self.charge_level.path_and_mask(mask)

        # Add elements to the list
        self.elements = [
            (self.case.shape, self.case.paint),
            (self.anode.shape, self.anode.paint),
        ]

        if self.level > 0:
            self.elements.append((self.charge_level.shape, self.charge_level.paint))
        if self.charging:
            self.elements.append((self.lightning_bolt.shape, self.lightning_bolt.paint))

        # Set SVG dimensions
        self.svg_width = self.anode.x_chord + (self.anode.r - (self.anode.r / 3))
        self.svg_height = self.case.height + self.case.stroke_width


class NumberBattery(Battery):
    def __init__(
        self,
        width: float = Battery.BASE_CASE_WIDTH,
        charging: bool = False,
        level: int = 100,
        font_path: Path = (FONTS_DIR / "OpenSans-Variable.ttf"),
    ):
        self.font_path = font_path
        super().__init__(width, charging, level)

    # TODO: Put number in the right place at the right size.  Pad to 2 digits minimum.  Figure out masking.
    def _assemble(self) -> None:
        self.case = BatteryCase(self.width)
        self.anode = Anode(self.case)
        self.charge_level = BatteryChargeLevel(self.case, self.charging, self.level)

        # Determine lightning bolt offsets:
        bolt_x_offset_percentage = 0.75
        bolt_y_offset_percentage = 0.73
        lightning_bolt_total_scale = 0.5

        self.lightning_bolt = LightningBolt(
            self.case.x,
            self.case.y,
            self.case.width,
            self.case.height,
            bolt_x_offset_percentage,
            bolt_y_offset_percentage,
            lightning_bolt_total_scale,
        )
        self.lightning_bolt_mask = LightningBolt(
            self.case.x,
            self.case.y,
            self.case.width,
            self.case.height,
            bolt_x_offset_percentage,
            bolt_y_offset_percentage,
            lightning_bolt_total_scale,
            stroke_width=4,
        )
        self.number = Number(
            base_x=self.case.x + (self.case.width * 0.1),
            base_y=self.case.y + (self.case.height * 0.1),
            base_width=self.case.width * 0.8,
            base_height=self.case.height * 0.8,
            x_offset_pct=0.1,
            font_path=self.font_path,
            level=self.level,
            total_scale=self.transform_scale,
        )

        bolt_mask = self.lightning_bolt_mask.shape if self.charging else None
        number_mask = self.number.bounding_box
        self.case.path_and_mask(bolt_mask)
        self.charge_level.path_and_mask(bolt_mask)
        self.charge_level.path_and_mask(number_mask)
        # self.number.path_and_mask(number_mask)

        # Add elements to the list
        self.elements = [
            (self.case.shape, self.case.paint),
            (self.anode.shape, self.anode.paint),
        ]

        if self.level > 0:
            self.elements.append((self.charge_level.shape, self.charge_level.paint))
        if self.charging:
            self.elements.append((self.lightning_bolt.shape, self.lightning_bolt.paint))

        self.elements.append((self.number.shape, self.number.paint))

        # Set SVG dimensions
        self.svg_width = self.anode.x_chord + (self.anode.r - (self.anode.r / 3))
        self.svg_height = self.case.height + self.case.stroke_width
