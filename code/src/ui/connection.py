"""Bezier curve connections between output and input ports."""

import pyray as rl

from src.ui.colors import CONNECTION_LINE, CONNECTION_DOT
from src.ui.types import CardState, ConnectionInfo
from src.ui.card import output_port_position, input_port_position

# ── Constants ───────────────────────────────────────────────────────
CURVE_SEGMENTS = 32
CURVE_THICKNESS = 1.5
MIDPOINT_RADIUS = 4
HIT_RADIUS = 12.0              # click tolerance around the midpoint
PAIR_SPREAD = 14.0             # vertical pixels between curves of the same pair


# ── Cubic bezier helpers ────────────────────────────────────────────

def _bezier_point(
    p0: rl.Vector2, p1: rl.Vector2, p2: rl.Vector2, p3: rl.Vector2, t: float,
) -> rl.Vector2:
    u = 1.0 - t
    return rl.Vector2(
        u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
        u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y,
    )


def _control_points(
    start: rl.Vector2,
    end: rl.Vector2,
    pair_index: int = 0,
    pair_count: int = 1,
) -> tuple:
    """Horizontal-offset control points for a smooth S-curve.

    When multiple connections share the same model pair, they are spread
    vertically via *pair_index* / *pair_count* so the curves fan out
    instead of overlapping.
    """
    dx = abs(end.x - start.x) * 0.45
    dx = max(dx, 60.0)

    # Vertical offset: centre the group around 0
    if pair_count > 1:
        offset = (pair_index - (pair_count - 1) / 2.0) * PAIR_SPREAD
    else:
        offset = 0.0

    cp1 = rl.Vector2(start.x + dx, start.y + offset)
    cp2 = rl.Vector2(end.x - dx, end.y + offset)
    return cp1, cp2


# ── Public API ──────────────────────────────────────────────────────

def connection_endpoints(
    conn: ConnectionInfo,
    cards: dict[str, CardState],
) -> tuple[rl.Vector2, rl.Vector2] | None:
    """Return (start, end) world positions for a connection, or None."""
    from_card = cards.get(conn.from_model_id)
    to_card = cards.get(conn.to_model_id)
    if from_card is None or to_card is None:
        return None
    start = output_port_position(from_card, conn.from_port_index)
    end = input_port_position(to_card, conn.to_port_index)
    return start, end


def connection_midpoint(
    start: rl.Vector2, end: rl.Vector2,
    pair_index: int = 0, pair_count: int = 1,
) -> rl.Vector2:
    cp1, cp2 = _control_points(start, end, pair_index, pair_count)
    return _bezier_point(start, cp1, cp2, end, 0.5)


def is_near_midpoint(
    wx: float, wy: float,
    conn: ConnectionInfo,
    cards: dict[str, CardState],
) -> bool:
    pts = connection_endpoints(conn, cards)
    if pts is None:
        return False
    start, end = pts
    mid = connection_midpoint(start, end, conn.pair_index, conn.pair_count)
    ddx = wx - mid.x
    ddy = wy - mid.y
    return (ddx * ddx + ddy * ddy) <= HIT_RADIUS * HIT_RADIUS


def draw_connection(
    conn: ConnectionInfo,
    cards: dict[str, CardState],
) -> None:
    """Draw a single bezier connection with a midpoint dot."""
    pts = connection_endpoints(conn, cards)
    if pts is None:
        return
    start, end = pts
    cp1, cp2 = _control_points(start, end, conn.pair_index, conn.pair_count)

    # Draw the curve as line segments
    prev = start
    for i in range(1, CURVE_SEGMENTS + 1):
        t = i / CURVE_SEGMENTS
        curr = _bezier_point(start, cp1, cp2, end, t)
        rl.draw_line_ex(prev, curr, CURVE_THICKNESS, CONNECTION_LINE)
        prev = curr

    # Midpoint dot
    mid = _bezier_point(start, cp1, cp2, end, 0.5)
    rl.draw_circle(int(mid.x), int(mid.y), MIDPOINT_RADIUS, CONNECTION_DOT)
