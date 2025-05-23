from math import sqrt
from svg import SVG, ViewBoxSpec, M, A, Z, Rect, Path, Arc, l, c, h, L, C, H, V, v, m
from pathlib import Path as PPath


class BatteryCase:
    """
    Represents the outer battery case with configurable width.
    Height is set to half the width, stroke-width is width/20,
    corner radius is width/8 by default.
    """
    def __init__(self, width):
        self.width = width
        self.stroke_width = width / 20
        self.height = width / 2
        self.rx = width / 8 # Or just always 15?
        self.ry = self.rx
        self.x = self.stroke_width / 2
        self.y = self.stroke_width / 2
        self.fill = "none"
        self.stroke = "black"

    def draw(self, elem_id="battery-case"):
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
            id=elem_id
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
        self.cy = (battery_case.y + battery_case.height + battery_case.stroke_width / 2) / 2
        delta_y = sqrt(self.r ** 2 - delta_x ** 2)
        self.y1 = self.cy - delta_y
        self.y2 = self.cy + delta_y
        self.fill = battery_case.stroke

    def draw(self, elem_id="anode"):
        return Path(
            d=[
                M(self.x_chord,self.y1),
                Arc(rx=self.r, ry=self.r, angle=0, large_arc=False, sweep=True, x=self.x_chord, y=self.y2),
                Z()
            ],
            stroke="none",
            fill=self.fill,
            id=elem_id
        )
        # doc.path(d=path_d, fill=self.fill, stroke="none", id=elem_id)


class BatteryChargeLevel:
    """
    Represents the charge level of the battery.
    """
    def __init__(self, battery_case: BatteryCase, charging: bool = False, charge_level: int = 100):
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
        # self.fill_color = "yellow" if self.charging else "gray"
        self.fill_color = "black"
        self.id = "charge-level"
        # self.id = "charge" if self.charging else "drain"
        # self.id = f"{self.id}{self.charge_level}"

    def draw(self, elem_id="charge_level"):
        return Rect(
            x=self.x,
            y=self.y,
            width=self.fill_width,
            height=self.height,
            rx=self.rx,
            ry=self.ry,
            fill=self.fill_color,
            stroke="none",
            id=self.id
        )


class LightningBolt:
    """
    Contains the LightningBolt, scaled and centered
    based on the size of the BatteryCase.
    """
    def __init__(self, battery_case, base_width, stroke_width=0, color="black"):
        self.stroke_width = stroke_width
        self.fill_color = color
        # 1) grab case dims
        bc_width, bc_height = battery_case.width, battery_case.height
        bc_x, bc_y = battery_case.x, battery_case.y

        transform_scale = (bc_width / base_width)

        # 2) define raw bolt as svg.py command-objects (absolute coords)
        raw = [
            M(57.12, 60.58),
            l(23.51, -29.46),
            c(.44, -.59, .68, -1.16, .68, -1.71),
            c(0, -1.06, -.86, -1.86, -1.96, -1.86),
            h(-14.48),
            l(7.72, -20.77),
            c(.65, -1.84, -.42, -3.13, -1.72, -3.13),
            c(-.65, 0, -1.35, .32, -1.93, 1.05),
            l(-23.51, 29.47),
            c(-.44, .59, -.73, 1.15, -.73, 1.70),
            c(0, 1.06, .90, 1.86, 1.97, 1.86),
            h(14.51),
            l(-7.72, 20.81),
            c(-.68, 1.83, .39, 3.10, 1.70, 3.10),
            c(.66, 0, 1.38, -.32, 1.96, -1.06),
            Z()
        ]

        if transform_scale != 1:

            # 3) compute original bounding box
            x = y = 0.0
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')

            for cmd in raw:
                if isinstance(cmd, M):
                    # absolute MoveTo
                    x, y = cmd.x, cmd.y
                elif isinstance(cmd, m):
                    # relative moveto
                    x += cmd.dx
                    y += cmd.dy
                elif isinstance(cmd, L):
                    # absolute LineTo
                    x, y = cmd.x, cmd.y
                elif isinstance(cmd, l):
                    # relative line to
                    x += cmd.dx
                    y += cmd.dy
                elif isinstance(cmd, H):
                    # absolute horizontal line
                    x = cmd.x
                elif isinstance(cmd, h):
                    # relative horizontal line
                    x += cmd.dx
                elif isinstance(cmd, V):
                    # absolute vertical line
                    y = cmd.y
                elif isinstance(cmd, v):
                    # relative vertical line
                    y += cmd.dy
                elif isinstance(cmd, C):
                    # absolute cubic Bézier; .x,.y is endpoint
                    x, y = cmd.x, cmd.y
                elif isinstance(cmd, c):
                    # relative cubic Bézier; dx,dy is endpoint offset
                    x += cmd.dx
                    y += cmd.dy
                # Z() resets back to start of subpath but doesn't move the pen
                # so, we just ignore it for bbox purposes

                # update our min/max
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

            bolt_w = max_x - min_x
            bolt_h = max_y - min_y

            # 4) figure out scale + center-offset
            scale = min(bc_width / bolt_w, bc_height / bolt_h)
            offset_x = bc_x + (bc_width - bolt_w * scale) / 2 - min_x * scale
            offset_y = bc_y + (bc_height - bolt_h * scale) / 2 - min_y * scale

            # 5) rebuild scaled commands
            cmds = []
            for cmd in raw:
                if isinstance(cmd, M):
                    cmds.append(M(
                        cmd.x * scale + offset_x,
                        cmd.y * scale + offset_y
                    ))
                elif isinstance(cmd, m):
                    cmds.append(m(
                        cmd.dx * scale,
                        cmd.dy * scale
                    ))
                elif isinstance(cmd, L):
                    print("got L")
                    cmds.append(L(
                        cmd.x * scale + offset_x,
                        cmd.y * scale + offset_y
                    ))
                elif isinstance(cmd, l):
                    cmds.append(l(
                        cmd.dx * scale,
                        cmd.dy * scale
                    ))
                elif isinstance(cmd, H):
                    print("got H")
                    cmds.append(H(cmd.x * scale + offset_x))
                elif isinstance(cmd, h):
                    cmds.append(h(cmd.dx * scale))
                elif isinstance(cmd, V):
                    print("got H")
                    cmds.append(V(cmd.y * scale + offset_x))
                elif isinstance(cmd, v):
                    cmds.append(v(cmd.dy * scale))
                elif isinstance(cmd, C):
                    print("got C")
                    cmds.append(C(
                        cmd.x1 * scale + offset_x, cmd.y1 * scale + offset_y,
                        cmd.x2 * scale + offset_x, cmd.y2 * scale + offset_y,
                        cmd.x  * scale + offset_x, cmd.y  * scale + offset_y
                    ))
                elif isinstance(cmd, c):
                    cmds.append(c(
                        cmd.dx1 * scale, cmd.dy1 * scale,
                        cmd.dx2 * scale, cmd.dy2 * scale,
                        cmd.dx * scale, cmd.dy * scale
                    ))
                elif isinstance(cmd, Z):
                    cmds.append(Z())
                else:  # Z()
                    print(f"Got type I can't process: {type(cmd)}")

            # store for draw()
            self.commands = cmds
        else:
            self.commands = raw

    def draw(self, elem_id="lightning-bolt"):
        return Path(
            d=self.commands,
            fill=self.fill_color,
            stroke=self.fill_color,
            stroke_width=self.stroke_width,
            id=elem_id
        )


class Battery:
    """
    Combines BatteryCase, Anode, BatteryChargeLevel, and LightningBolt
    and renders the complete battery SVG, with configurable charge state
    and level.
    """
    def __init__(self, width, charging=False, level=100):
        self.base_battery_case_width = 120
        self.case = BatteryCase(width)
        self.anode = Anode(self.case)
        self.charging = charging
        # clamp level between 0 and 100
        self.level = max(0, min(100, level))
        self.charge_level = BatteryChargeLevel(self.case, self.charging, self.level)
        self.lightning_bolt = LightningBolt(self.case, self.base_battery_case_width)
        self.lightning_bolt_mask = LightningBolt(self.case, self.base_battery_case_width, 12)



    def build_svg(self):
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
            elements=elements
        )
        return doc


if __name__ == "__main__":
    script_dir = PPath(__file__).parent
    build_dir = script_dir.joinpath("build")
    raw_dir = build_dir.joinpath("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    charge_dir = raw_dir.joinpath("charging")
    charge_dir.mkdir(parents=True, exist_ok=True)
    discharge_dir = raw_dir.joinpath("discharging")
    discharge_dir.mkdir(parents=True, exist_ok=True)

    for charge in [True, False]:
        for i in range(101):
            glyph_name = f"battery_{'charge' if charge else 'discharge'}_{i:0>3}.svg"
            out_dir = charge_dir if charge else discharge_dir
            glyph_path = out_dir.joinpath(glyph_name)

            glyph = Battery(width=120, charging=charge, level=i)
            svg_doc = glyph.build_svg()

            with glyph_path.open('w') as f:
                f.write(str(svg_doc))
