"""Atomics Graphs – imgui-bundle implementation with zoom & pan."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from imgui_bundle import imgui, immapp, hello_imgui


# ── Data Model ──────────────────────────────────────────────────────────────

@dataclass
class Port:
    name: str
    is_input: bool

@dataclass
class AtomicBlock:
    name: str
    x: float
    y: float
    w: float = 200.0
    h: float = 120.0
    ta: float = 0.02
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    color: tuple = (0, 128, 128)  # teal header

@dataclass
class CoupledModel:
    name: str
    x: float
    y: float
    w: float
    h: float
    children: list[AtomicBlock] = field(default_factory=list)


# ── Board State ─────────────────────────────────────────────────────────────

class BoardState:
    def __init__(self):
        self.offset_x = 50.0
        self.offset_y = 80.0
        self.zoom = 1.0
        self.dragging = False
        self.last_mouse_x = 0.0
        self.last_mouse_y = 0.0

        # Build the model
        manufacturing = AtomicBlock(
            "Manufacturing", 30, 30, 200, 120,
            inputs=[Port("Intermediates", True), Port("Messages", True)],
            outputs=[Port("Production", False), Port("Messages", False)],
        )
        administration = AtomicBlock(
            "Administration", 280, 150, 200, 120,
            inputs=[Port("Intermediates", True), Port("Messages", True)],
            outputs=[Port("Production", False), Port("Messages", False)],
        )
        rnd = AtomicBlock(
            "R&D", 30, 270, 200, 120,
            inputs=[Port("Intermediates", True), Port("Messages", True)],
            outputs=[Port("Production", False), Port("Messages", False)],
        )
        self.company = CoupledModel("Company", 0, 0, 530, 430, [manufacturing, administration, rnd])

        self.goods_market = AtomicBlock(
            "Goods Market", 580, 300, 200, 120,
            inputs=[Port("Intermediates", True), Port("Messages", True)],
            outputs=[Port("Production", False), Port("Messages", False)],
        )

    def screen_pos(self, x: float, y: float):
        return (self.offset_x + x * self.zoom, self.offset_y + y * self.zoom)


STATE = BoardState()


# ── Drawing Helpers ─────────────────────────────────────────────────────────

def col32(r, g, b, a=255):
    return imgui.color_convert_float4_to_u32(imgui.ImVec4(r / 255, g / 255, b / 255, a / 255))


def draw_port_dot(dl, cx, cy, radius):
    dl.add_circle_filled(imgui.ImVec2(cx, cy), radius, col32(70, 150, 200), 12)
    dl.add_circle(imgui.ImVec2(cx, cy), radius, col32(40, 100, 140), 12, 1.0)


def draw_atomic(dl: imgui.ImDrawList, block: AtomicBlock, base_x: float, base_y: float):
    s = STATE
    z = s.zoom
    bx, by = s.screen_pos(base_x + block.x, base_y + block.y)
    bw, bh = block.w * z, block.h * z

    if z < 0.35:
        # Zoom level 3: just a small rect with dots
        dl.add_rect_filled(imgui.ImVec2(bx, by), imgui.ImVec2(bx + bw, by + bh), col32(220, 220, 220))
        dl.add_rect(imgui.ImVec2(bx, by), imgui.ImVec2(bx + bw, by + bh), col32(60, 60, 60), 0, 0, 1.0)
        dot_r = max(2, 3 * z / 0.35)
        draw_port_dot(dl, bx, by + bh * 0.5, dot_r)
        draw_port_dot(dl, bx + bw, by + bh * 0.5, dot_r)
        return

    if z < 0.7:
        # Zoom level 2: rect + name + port dots
        dl.add_rect_filled(imgui.ImVec2(bx, by), imgui.ImVec2(bx + bw, by + bh), col32(230, 230, 230))
        dl.add_rect(imgui.ImVec2(bx, by), imgui.ImVec2(bx + bw, by + bh), col32(60, 60, 60), 0, 0, 1.0)
        font_scale = z / 0.7
        name = block.name
        text_size = imgui.calc_text_size(name)
        tx = bx + (bw - text_size.x * font_scale) * 0.5
        ty = by + (bh - text_size.y * font_scale) * 0.5
        dl.add_text(
            imgui.get_font(), imgui.get_font_size() * font_scale,
            imgui.ImVec2(tx, ty), col32(30, 30, 30), name
        )
        dot_r = max(2, 4 * z)
        n_in = len(block.inputs)
        for i in range(n_in):
            py = by + bh * (i + 1) / (n_in + 1)
            draw_port_dot(dl, bx, py, dot_r)
        n_out = len(block.outputs)
        for i in range(n_out):
            py = by + bh * (i + 1) / (n_out + 1)
            draw_port_dot(dl, bx + bw, py, dot_r)
        return

    # Zoom level 1: full detail
    header_h = 26 * z
    # Header
    dl.add_rect_filled(imgui.ImVec2(bx, by), imgui.ImVec2(bx + bw, by + header_h),
                       col32(*block.color))
    # Body
    dl.add_rect_filled(imgui.ImVec2(bx, by + header_h), imgui.ImVec2(bx + bw, by + bh),
                       col32(235, 235, 235))
    # Border
    dl.add_rect(imgui.ImVec2(bx, by), imgui.ImVec2(bx + bw, by + bh), col32(60, 60, 60), 0, 0, 1.0)
    # Separator above ta
    ta_h = 20 * z
    dl.add_line(imgui.ImVec2(bx, by + bh - ta_h), imgui.ImVec2(bx + bw, by + bh - ta_h),
                col32(180, 180, 180), 1.0)

    font_size_scale = min(1.0, z)
    fs = imgui.get_font_size() * font_size_scale
    font = imgui.get_font()

    # Header text
    dl.add_text(font, fs, imgui.ImVec2(bx + 6 * z, by + 4 * z), col32(255, 255, 255), block.name)

    # Port labels + dots
    port_y_start = by + header_h + 8 * z
    line_h = 18 * z
    dot_r = max(2, 4 * z)

    for i, p in enumerate(block.inputs):
        py = port_y_start + i * line_h
        draw_port_dot(dl, bx, py + fs * 0.4, dot_r)
        dl.add_text(font, fs * 0.85, imgui.ImVec2(bx + 10 * z, py), col32(50, 50, 50), p.name)

    for i, p in enumerate(block.outputs):
        py = port_y_start + i * line_h
        draw_port_dot(dl, bx + bw, py + fs * 0.4, dot_r)
        ts = imgui.calc_text_size(p.name)
        dl.add_text(font, fs * 0.85,
                       imgui.ImVec2(bx + bw - 10 * z - ts.x * font_size_scale * 0.85, py),
                       col32(50, 50, 50), p.name)

    # ta text
    ta_text = f"ta: {block.ta}s"
    dl.add_text(font, fs * 0.8, imgui.ImVec2(bx + 6 * z, by + bh - ta_h + 2 * z),
                   col32(120, 120, 120), ta_text)


def draw_coupled(dl: imgui.ImDrawList, model: CoupledModel):
    s = STATE
    z = s.zoom
    cx, cy = s.screen_pos(model.x, model.y)
    cw, ch = model.w * z, model.h * z

    # Dashed border
    dash_len = 12 * z
    gap_len = 8 * z
    thickness = max(1.0, 2.0 * z)
    edges = [
        ((cx, cy), (cx + cw, cy)),
        ((cx + cw, cy), (cx + cw, cy + ch)),
        ((cx + cw, cy + ch), (cx, cy + ch)),
        ((cx, cy + ch), (cx, cy)),
    ]
    for (x0, y0), (x1, y1) in edges:
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 1:
            continue
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        drawn = 0.0
        is_dash = True
        while drawn < length:
            seg = dash_len if is_dash else gap_len
            seg = min(seg, length - drawn)
            if is_dash:
                sx, sy = x0 + dx * drawn, y0 + dy * drawn
                ex, ey = sx + dx * seg, sy + dy * seg
                dl.add_line(imgui.ImVec2(sx, sy), imgui.ImVec2(ex, ey),
                            col32(50, 50, 50), thickness)
            drawn += seg
            is_dash = not is_dash

    # Label
    if z > 0.25:
        fs = imgui.get_font_size() * min(1.0, z)
        dl.add_text(imgui.get_font(), fs,
                       imgui.ImVec2(cx + 8 * z, cy - fs - 2 * z),
                       col32(40, 40, 40), model.name)

    for child in model.children:
        draw_atomic(dl, child, model.x, model.y)


# ── Main GUI ────────────────────────────────────────────────────────────────

def gui():
    s = STATE
    io = imgui.get_io()

    imgui.set_next_window_pos(imgui.ImVec2(0, 0))
    imgui.set_next_window_size(io.display_size)
    flags = (imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_resize |
             imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_scrollbar |
             imgui.WindowFlags_.no_scroll_with_mouse)
    imgui.begin("Atomics Graphs", None, flags)

    # Title bar
    imgui.text("Atomics Graphs")
    imgui.same_line(imgui.get_window_width() - 160)
    imgui.text(f"Zoom: {s.zoom:.2f}")
    imgui.same_line()
    if imgui.button("-"):
        s.zoom = max(0.15, s.zoom / 1.3)
    imgui.same_line()
    if imgui.button("+"):
        s.zoom = min(3.0, s.zoom * 1.3)

    # Canvas
    canvas_pos = imgui.get_cursor_screen_pos()
    canvas_size = imgui.get_content_region_avail()
    dl = imgui.get_window_draw_list()

    # Background
    dl.add_rect_filled(
        canvas_pos,
        imgui.ImVec2(canvas_pos.x + canvas_size.x, canvas_pos.y + canvas_size.y),
        col32(190, 190, 190)
    )

    # Invisible button for interaction
    imgui.invisible_button("canvas", canvas_size)
    is_hovered = imgui.is_item_hovered()

    # Zoom with scroll
    if is_hovered and abs(io.mouse_wheel) > 0:
        mx, my = io.mouse_pos.x, io.mouse_pos.y
        old_zoom = s.zoom
        factor = 1.15 if io.mouse_wheel > 0 else 1.0 / 1.15
        s.zoom = max(0.15, min(3.0, s.zoom * factor))
        # Zoom toward mouse
        s.offset_x = mx - (mx - s.offset_x) * (s.zoom / old_zoom)
        s.offset_y = my - (my - s.offset_y) * (s.zoom / old_zoom)

    # Pan with mouse drag
    if is_hovered and imgui.is_mouse_dragging(imgui.MouseButton_.left, 1.0):
        delta = io.mouse_delta
        s.offset_x += delta.x
        s.offset_y += delta.y

    # Draw
    dl.push_clip_rect(canvas_pos,
                      imgui.ImVec2(canvas_pos.x + canvas_size.x, canvas_pos.y + canvas_size.y), True)
    draw_coupled(dl, s.company)
    draw_atomic(dl, s.goods_market, 0, 0)
    dl.pop_clip_rect()

    imgui.end()


def main():
    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = "Atomics Graphs"
    params.app_window_params.window_geometry.size = (1100, 750)
    params.callbacks.show_gui = gui
    params.fps_idling.fps_idle = 30.0
    immapp.run(params)


if __name__ == "__main__":
    main()