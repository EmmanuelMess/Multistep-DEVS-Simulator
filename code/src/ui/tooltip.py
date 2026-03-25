"""Dashed-border message-inspector tooltip shown on connection click."""

import pyray as rl

from src.ui.colors import TOOLTIP_BG, TOOLTIP_BORDER, TOOLTIP_TEXT
from src.ui.types import TooltipState

# ── Constants ───────────────────────────────────────────────────────
ROW_HEIGHT = 18
PAD_X = 10
PAD_Y = 8
FONT_SIZE = 11
DASH_LENGTH = 6
GAP_LENGTH = 4
BORDER_THICKNESS = 1.5
COUNT_COL_WIDTH = 50      # right-aligned count column


# ── Drawing ─────────────────────────────────────────────────────────

def _draw_dashed_rect(x: float, y: float, w: float, h: float) -> None:
    """Draw a rectangle with dashed edges."""
    edges = [
        (x, y, x + w, y),          # top
        (x + w, y, x + w, y + h),  # right
        (x + w, y + h, x, y + h),  # bottom
        (x, y + h, x, y),          # left
    ]
    for x0, y0, x1, y1 in edges:
        length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if length == 0:
            continue
        dx = (x1 - x0) / length
        dy = (y1 - y0) / length
        d = 0.0
        drawing = True
        while d < length:
            seg = DASH_LENGTH if drawing else GAP_LENGTH
            seg = min(seg, length - d)
            if drawing:
                rl.draw_line_ex(
                    rl.Vector2(x0 + dx * d, y0 + dy * d),
                    rl.Vector2(x0 + dx * (d + seg), y0 + dy * (d + seg)),
                    BORDER_THICKNESS,
                    TOOLTIP_BORDER,
                )
            d += seg
            drawing = not drawing


def draw_tooltip(state: TooltipState) -> None:
    """Draw the tooltip popup if visible."""
    if not state.visible or not state.stats:
        return

    # Compute box size
    max_name_w = max(rl.measure_text(s.type_name, FONT_SIZE) for s in state.stats)
    box_w = PAD_X + max_name_w + 20 + COUNT_COL_WIDTH + PAD_X
    box_h = PAD_Y + len(state.stats) * ROW_HEIGHT + PAD_Y

    bx = state.x
    by = state.y

    # Background
    rl.draw_rectangle(int(bx), int(by), int(box_w), int(box_h), TOOLTIP_BG)

    # Dashed border
    _draw_dashed_rect(bx, by, box_w, box_h)

    # Rows
    for i, stat in enumerate(state.stats):
        ry = by + PAD_Y + i * ROW_HEIGHT
        # Name (left-aligned)
        rl.draw_text(stat.type_name, int(bx + PAD_X), int(ry), FONT_SIZE, TOOLTIP_TEXT)
        # Count (right-aligned)
        count_str = str(stat.count)
        tw = rl.measure_text(count_str, FONT_SIZE)
        rl.draw_text(count_str, int(bx + box_w - PAD_X - tw), int(ry), FONT_SIZE, TOOLTIP_TEXT)
