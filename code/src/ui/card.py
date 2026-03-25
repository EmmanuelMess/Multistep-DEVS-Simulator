"""Atomic model card: layout constants, rendering, and hit-testing."""

from math import inf
from typing import List

import pyray as rl

from src.devs.Atomic import Atomic
from src.devs.Types import Port
from src.ui.colors import (
    HEADER_BG, HEADER_TEXT, CARD_BG, CARD_BORDER, CARD_DIVIDER,
    PORT_DOT, PORT_TEXT, DRAG_HANDLE, FOOTER_TEXT, SELECTION_OUTLINE,
)
from src.ui.types import CardState, PortInfo

# ── Layout constants ────────────────────────────────────────────────
CARD_MIN_WIDTH = 220
CARD_MAX_WIDTH = 420
HEADER_HEIGHT = 28
PORTS_PAD_TOP = 4
PORTS_PAD_BOTTOM = 4
PORT_LINE_HEIGHT = 16
PORT_DOT_RADIUS = 4
PORT_LABEL_FONT_SIZE = 10
PORT_LABEL_MARGIN = 12          # horizontal gap between dot and text
BODY_SECTION_HEIGHT = 30
FOOTER_HEIGHT = 18
HEADER_FONT_SIZE = 13
FOOTER_FONT_SIZE = 10
BORDER_THICKNESS = 1.0
SELECTION_PAD = 6               # extra padding for selection outline
SELECTION_THICKNESS = 2.0
SELECTION_CORNER_RADIUS = 8

# Drag handle (2-col x 3-row dot grid in header)
DRAG_DOT_RADIUS = 2
DRAG_DOT_COLS = 2
DRAG_DOT_ROWS = 3
DRAG_DOT_SPACING = 5


# ── Helpers ─────────────────────────────────────────────────────────

def _port_name_from_attr(model: Atomic, port: Port, is_input: bool) -> str:
    """Derive a readable name by inspecting class-level port constants.

    Keeps target qualifiers (_MFG, _RD) so that duplicate port types
    on the same model remain distinguishable.
    """
    suffix = "_IN" if is_input else "_OUT"
    for attr in dir(model.__class__):
        if attr.startswith("_"):
            continue
        val = getattr(model.__class__, attr, None)
        if isinstance(val, tuple) and len(val) == 2 and val == port:
            name = attr
            if name.endswith(suffix):
                name = name[: -len(suffix)]
            return name.replace("_", " ").title()
    # Fallback: use the type class name
    return port[1].__name__


def _display_name(model_id: str) -> str:
    """Extract a readable name from an id like '<manufacturing:1>'."""
    if model_id.startswith("<") and model_id.endswith(">"):
        name = model_id[1:-1].split(":")[0]
        return name.replace("_", " ").title()
    return model_id


# Approximate character width as a fraction of font size (for the
# default raylib font).  Used to size cards before the window opens.
_CHAR_WIDTH_FACTOR = 0.62
_MIN_PORT_GAP = 20          # minimum pixels between left and right labels


def _estimate_text_width(text: str, font_size: int) -> float:
    return len(text) * font_size * _CHAR_WIDTH_FACTOR


def _compute_card_width(in_ports: List[PortInfo], out_ports: List[PortInfo],
                        display_name: str) -> float:
    """Return a card width that fits all port-label pairs without overlap."""
    max_pair = 0.0
    n = max(len(in_ports), len(out_ports), 1)
    for i in range(n):
        left_w = 0.0
        right_w = 0.0
        if i < len(in_ports):
            left_w = _estimate_text_width(in_ports[i].name, PORT_LABEL_FONT_SIZE)
        if i < len(out_ports):
            right_w = _estimate_text_width(out_ports[i].name, PORT_LABEL_FONT_SIZE)
        max_pair = max(max_pair, left_w + right_w)

    needed = PORT_LABEL_MARGIN * 2 + max_pair + _MIN_PORT_GAP
    header_w = _estimate_text_width(display_name, HEADER_FONT_SIZE) + 40
    return max(CARD_MIN_WIDTH, min(CARD_MAX_WIDTH, needed, ), min(CARD_MAX_WIDTH, header_w))


def build_card(model: Atomic, x: float, y: float) -> CardState:
    """Create a CardState for *model* at the given canvas position."""
    in_ports = [
        PortInfo(port=p, name=_port_name_from_attr(model, p, True), is_input=True)
        for p in model.input_ports
    ]
    out_ports = [
        PortInfo(port=p, name=_port_name_from_attr(model, p, False), is_input=False)
        for p in model.output_ports
    ]
    name = _display_name(model.id)
    width = _compute_card_width(in_ports, out_ports, name)
    card = CardState(
        model_id=model.id,
        display_name=name,
        x=x,
        y=y,
        width=width,
        input_ports=in_ports,
        output_ports=out_ports,
    )
    card.height = compute_card_height(card)
    return card


# ── Geometry ────────────────────────────────────────────────────────

def compute_card_height(card: CardState) -> float:
    n = max(len(card.input_ports), len(card.output_ports), 1)
    ports_h = PORTS_PAD_TOP + n * PORT_LINE_HEIGHT + PORTS_PAD_BOTTOM
    return HEADER_HEIGHT + ports_h + 1 + BODY_SECTION_HEIGHT + 1 + BODY_SECTION_HEIGHT + FOOTER_HEIGHT


def port_screen_y(card: CardState, port_index: int) -> float:
    """Y-centre of the *port_index*-th port line on a card."""
    return card.y + HEADER_HEIGHT + PORTS_PAD_TOP + port_index * PORT_LINE_HEIGHT + PORT_LINE_HEIGHT / 2


def input_port_position(card: CardState, port_index: int) -> rl.Vector2:
    """World position of an input port dot (left edge)."""
    return rl.Vector2(card.x, port_screen_y(card, port_index))


def output_port_position(card: CardState, port_index: int) -> rl.Vector2:
    """World position of an output port dot (right edge)."""
    return rl.Vector2(card.x + card.width, port_screen_y(card, port_index))


def is_point_in_header(card: CardState, wx: float, wy: float) -> bool:
    return (card.x <= wx <= card.x + card.width
            and card.y <= wy <= card.y + HEADER_HEIGHT)


def is_point_in_card(card: CardState, wx: float, wy: float) -> bool:
    return (card.x <= wx <= card.x + card.width
            and card.y <= wy <= card.y + card.height)


# ── Drawing ─────────────────────────────────────────────────────────

def _draw_drag_handle(card: CardState) -> None:
    """Draw the 2x3 dot-grid drag handle in the header top-right."""
    base_x = card.x + card.width - 18
    base_y = card.y + 7
    for row in range(DRAG_DOT_ROWS):
        for col in range(DRAG_DOT_COLS):
            cx = base_x + col * DRAG_DOT_SPACING
            cy = base_y + row * DRAG_DOT_SPACING
            rl.draw_circle(int(cx), int(cy), DRAG_DOT_RADIUS, DRAG_HANDLE)


def draw_card(card: CardState, model: Atomic, selected: bool = False) -> None:
    """Render a full model card at its current position."""
    x, y, w = int(card.x), int(card.y), int(card.width)
    h = int(card.height)

    # ── Selection outline ───────────────────────────────────────────
    if selected:
        sel_rect = rl.Rectangle(
            card.x - SELECTION_PAD,
            card.y - SELECTION_PAD,
            card.width + 2 * SELECTION_PAD,
            card.height + 2 * SELECTION_PAD,
        )
        rl.draw_rectangle_rounded(sel_rect, 0.04, 6, SELECTION_OUTLINE)

    # ── Card background + border ────────────────────────────────────
    rl.draw_rectangle(x, y, w, h, CARD_BG)
    rl.draw_rectangle_lines(x, y, w, h, CARD_BORDER)

    # ── Header bar ──────────────────────────────────────────────────
    rl.draw_rectangle(x, y, w, HEADER_HEIGHT, HEADER_BG)
    rl.draw_text(card.display_name, x + 8, y + 7, HEADER_FONT_SIZE, HEADER_TEXT)
    _draw_drag_handle(card)

    # ── Port labels + dots ──────────────────────────────────────────
    n_lines = max(len(card.input_ports), len(card.output_ports), 1)
    for i in range(n_lines):
        py = port_screen_y(card, i)

        # Input port (left)
        if i < len(card.input_ports):
            info = card.input_ports[i]
            rl.draw_circle(int(card.x), int(py), PORT_DOT_RADIUS, PORT_DOT)
            rl.draw_text(
                info.name,
                x + PORT_LABEL_MARGIN,
                int(py - PORT_LABEL_FONT_SIZE / 2),
                PORT_LABEL_FONT_SIZE,
                PORT_TEXT,
            )

        # Output port (right)
        if i < len(card.output_ports):
            info = card.output_ports[i]
            rl.draw_circle(int(card.x + card.width), int(py), PORT_DOT_RADIUS, PORT_DOT)
            tw = rl.measure_text(info.name, PORT_LABEL_FONT_SIZE)
            rl.draw_text(
                info.name,
                x + w - PORT_LABEL_MARGIN - tw,
                int(py - PORT_LABEL_FONT_SIZE / 2),
                PORT_LABEL_FONT_SIZE,
                PORT_TEXT,
            )

    # ── Dividers between sections ───────────────────────────────────
    ports_bottom = int(card.y + HEADER_HEIGHT
                       + PORTS_PAD_TOP + n_lines * PORT_LINE_HEIGHT + PORTS_PAD_BOTTOM)
    rl.draw_line(x, ports_bottom, x + w, ports_bottom, CARD_DIVIDER)
    mid_div = ports_bottom + BODY_SECTION_HEIGHT
    rl.draw_line(x, mid_div, x + w, mid_div, CARD_DIVIDER)

    # ── Footer: time advance ────────────────────────────────────────
    ta = model.time_advance()
    if ta == inf:
        ta_str = "ta: inf"
    else:
        ta_str = f"ta: {ta:.2f}s"
    rl.draw_text(ta_str, x + 6, y + h - FOOTER_HEIGHT + 4, FOOTER_FONT_SIZE, FOOTER_TEXT)
