"""Toolbar with play/pause toggle and simulation-time display."""

import math

import pyray as rl

from src.ui.colors import (
    TOOLBAR_BG, TOOLBAR_BORDER, BUTTON_BG, BUTTON_HOVER, BUTTON_ICON,
)

# ── Constants ───────────────────────────────────────────────────────
TOOLBAR_HEIGHT = 40
BUTTON_SIZE = 28
BUTTON_MARGIN = 8
BUTTON_X = BUTTON_MARGIN
BUTTON_Y = (TOOLBAR_HEIGHT - BUTTON_SIZE) // 2

TIME_LABEL_X = BUTTON_X + BUTTON_SIZE + 16
TIME_LABEL_Y = TOOLBAR_HEIGHT // 2 - 6
TIME_FONT_SIZE = 12


# ── Hit-testing ─────────────────────────────────────────────────────

def is_play_button_clicked(screen_x: float, screen_y: float) -> bool:
    """Check whether a screen-space click lands on the play/pause button."""
    return (BUTTON_X <= screen_x <= BUTTON_X + BUTTON_SIZE
            and BUTTON_Y <= screen_y <= BUTTON_Y + BUTTON_SIZE)


def is_in_toolbar(screen_y: float) -> bool:
    return screen_y <= TOOLBAR_HEIGHT


# ── Drawing ─────────────────────────────────────────────────────────

def draw_toolbar(screen_width: int, is_playing: bool, sim_time: float) -> None:
    """Draw the toolbar strip at the top of the window."""
    # Background
    rl.draw_rectangle(0, 0, screen_width, TOOLBAR_HEIGHT, TOOLBAR_BG)
    rl.draw_line(0, TOOLBAR_HEIGHT, screen_width, TOOLBAR_HEIGHT, TOOLBAR_BORDER)

    # Button background (hover-aware)
    mx, my = rl.get_mouse_x(), rl.get_mouse_y()
    hovered = is_play_button_clicked(mx, my)
    bg = BUTTON_HOVER if hovered else BUTTON_BG
    btn_rect = rl.Rectangle(BUTTON_X, BUTTON_Y, BUTTON_SIZE, BUTTON_SIZE)
    rl.draw_rectangle_rounded(btn_rect, 0.2, 4, bg)

    # Icon
    cx = BUTTON_X + BUTTON_SIZE // 2
    cy = BUTTON_Y + BUTTON_SIZE // 2
    if is_playing:
        # Pause icon: two vertical bars
        bar_w, bar_h = 4, 14
        gap = 4
        rl.draw_rectangle(cx - gap - bar_w, cy - bar_h // 2, bar_w, bar_h, BUTTON_ICON)
        rl.draw_rectangle(cx + gap, cy - bar_h // 2, bar_w, bar_h, BUTTON_ICON)
    else:
        # Play icon: right-pointing triangle
        v1 = rl.Vector2(cx - 5, cy - 8)
        v2 = rl.Vector2(cx - 5, cy + 8)
        v3 = rl.Vector2(cx + 8, cy)
        rl.draw_triangle(v1, v2, v3, BUTTON_ICON)

    # Simulation time label
    if math.isfinite(sim_time):
        time_str = f"t = {sim_time:.2f}"
    else:
        time_str = "t = inf (done)"
    rl.draw_text(time_str, TIME_LABEL_X, TIME_LABEL_Y, TIME_FONT_SIZE, BUTTON_ICON)
