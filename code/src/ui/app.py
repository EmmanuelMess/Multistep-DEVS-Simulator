"""Main application: window lifecycle, input handling, simulation stepping."""

import math
from collections import Counter
from typing import Dict, List, Optional, Tuple

import pyray as rl

from src.devs.AtomicGraph import AtomicGraph
from src.devs.Simulator import Simulator
from src.devs.Types import Id, Port
from src.ui.card import (
    build_card, draw_card, is_point_in_header, is_point_in_card,
)
from src.ui.colors import CANVAS_BG
from src.ui.connection import (
    draw_connection, is_near_midpoint, connection_endpoints, connection_midpoint,
)
from src.ui.toolbar import (
    TOOLBAR_HEIGHT, draw_toolbar, is_play_button_clicked, is_in_toolbar,
)
from src.ui.tooltip import draw_tooltip
from src.ui.types import AppState, CardState, ConnectionInfo, MessageStat, TooltipState

# ── Window defaults ─────────────────────────────────────────────────
DEFAULT_WIDTH = 1100
DEFAULT_HEIGHT = 720
WINDOW_TITLE = "Atomics Graphs"
TARGET_FPS = 60


class App:
    """Drives the raylib window and orchestrates all UI subsystems."""

    def __init__(self, graph: AtomicGraph, simulator: Simulator) -> None:
        self.graph = graph
        self.simulator = simulator
        self.state = AppState()
        self._build_state()

    # ── State construction from the DEVS graph ──────────────────────

    def _build_state(self) -> None:
        """Populate cards and connections from the AtomicGraph."""
        models = list(self.graph.models.values())

        # Sort models: output-only (sources) first, then by total
        # connection count descending so heavily-connected models sit
        # in the left column where output ports face right.
        def _sort_key(m):
            has_inputs = len(m.input_ports) > 0
            conn_count = sum(
                len(targets)
                for (oid, _), targets in self.graph._connections.items()
                if oid == m.id or any(tid == m.id for tid, _ in targets)
            )
            return (has_inputs, -conn_count)

        models.sort(key=_sort_key)

        # Build cards first (at origin) so we know their sizes
        temp_cards = [build_card(m, 0, 0) for m in models]

        # Auto-layout: 2-column grid with spacing derived from card sizes
        cols = min(len(models), 2) if models else 1
        max_w = max((c.width for c in temp_cards), default=240)
        max_h = max((c.height for c in temp_cards), default=200)
        spacing_x = max_w + 160
        spacing_y = max_h + 50
        start_x = 60.0
        start_y = 40.0

        for i, card in enumerate(temp_cards):
            col = i % cols
            row = i // cols
            card.x = start_x + col * spacing_x
            card.y = start_y + row * spacing_y
            self.state.cards[card.model_id] = card

        # Build connection list from graph._connections
        for (out_id, out_port), targets in self.graph._connections.items():
            out_card = self.state.cards.get(out_id)
            if out_card is None:
                continue
            out_idx = self._port_index(out_card, out_port, is_input=False)
            for in_id, in_port in targets:
                in_card = self.state.cards.get(in_id)
                if in_card is None:
                    continue
                in_idx = self._port_index(in_card, in_port, is_input=True)
                self.state.connections.append(ConnectionInfo(
                    from_model_id=out_id,
                    from_port=out_port,
                    from_port_index=out_idx,
                    to_model_id=in_id,
                    to_port=in_port,
                    to_port_index=in_idx,
                ))

        # Compute pair_index / pair_count so overlapping curves spread
        pair_counts: Counter = Counter()
        for conn in self.state.connections:
            key = (conn.from_model_id, conn.to_model_id)
            pair_counts[key] += 1

        pair_seen: dict = {}
        for conn in self.state.connections:
            key = (conn.from_model_id, conn.to_model_id)
            idx = pair_seen.get(key, 0)
            conn.pair_index = idx
            conn.pair_count = pair_counts[key]
            pair_seen[key] = idx + 1

    @staticmethod
    def _port_index(card: CardState, port: Port, is_input: bool) -> int:
        ports = card.input_ports if is_input else card.output_ports
        for i, info in enumerate(ports):
            if info.port == port:
                return i
        return 0

    # ── Main loop ───────────────────────────────────────────────────

    def run(self) -> None:
        rl.init_window(DEFAULT_WIDTH, DEFAULT_HEIGHT, WINDOW_TITLE)
        rl.set_target_fps(TARGET_FPS)
        rl.set_window_state(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE)

        while not rl.window_should_close():
            self._handle_input()
            self._update()
            self._draw()

        rl.close_window()

    # ── Input handling ──────────────────────────────────────────────

    def _screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        """Convert screen coords to canvas world coords."""
        return sx - self.state.camera_x, sy - TOOLBAR_HEIGHT - self.state.camera_y

    def _handle_input(self) -> None:
        mx = float(rl.get_mouse_x())
        my = float(rl.get_mouse_y())
        wx, wy = self._screen_to_world(mx, my)

        # ── Play / Pause button ─────────────────────────────────────
        if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
            if is_play_button_clicked(mx, my):
                self.state.is_playing = not self.state.is_playing
                self.state.step_accumulator = 0.0
                return

        # Ignore canvas interactions when clicking the toolbar
        if is_in_toolbar(my):
            return

        # ── Left click: card drag / select / tooltip ────────────────
        if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
            self.state.tooltip.visible = False
            clicked_card: Optional[Id] = None

            # Check cards (reverse draw order = front first)
            for card in reversed(list(self.state.cards.values())):
                if is_point_in_header(card, wx, wy):
                    card.is_dragging = True
                    card.drag_offset_x = wx - card.x
                    card.drag_offset_y = wy - card.y
                    clicked_card = card.model_id
                    break
                if is_point_in_card(card, wx, wy):
                    clicked_card = card.model_id
                    break

            if clicked_card is not None:
                self.state.selected_card = clicked_card
            else:
                self.state.selected_card = None
                # Check connection midpoints
                for i, conn in enumerate(self.state.connections):
                    if is_near_midpoint(wx, wy, conn, self.state.cards):
                        self._show_tooltip(i, wx, wy)
                        break

        # ── Left drag: move card ────────────────────────────────────
        if rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_LEFT):
            for card in self.state.cards.values():
                if card.is_dragging:
                    card.x = wx - card.drag_offset_x
                    card.y = wy - card.drag_offset_y

        if rl.is_mouse_button_released(rl.MouseButton.MOUSE_BUTTON_LEFT):
            for card in self.state.cards.values():
                card.is_dragging = False

        # ── Right-drag: pan canvas ──────────────────────────────────
        if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_RIGHT):
            self.state.is_panning = True
            self.state.pan_start_x = mx - self.state.camera_x
            self.state.pan_start_y = my - self.state.camera_y

        if rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_RIGHT) and self.state.is_panning:
            self.state.camera_x = mx - self.state.pan_start_x
            self.state.camera_y = my - self.state.pan_start_y

        if rl.is_mouse_button_released(rl.MouseButton.MOUSE_BUTTON_RIGHT):
            self.state.is_panning = False

    # ── Tooltip ─────────────────────────────────────────────────────

    def _show_tooltip(self, conn_idx: int, wx: float, wy: float) -> None:
        conn = self.state.connections[conn_idx]
        type_name = conn.to_port[1].__name__
        self.state.tooltip = TooltipState(
            visible=True,
            x=wx + 12,
            y=wy - 10,
            connection_idx=conn_idx,
            stats=[MessageStat(type_name=type_name, count=conn.message_count)],
        )

    # ── Simulation stepping ─────────────────────────────────────────

    def _update(self) -> None:
        if not self.state.is_playing:
            return

        dt = rl.get_frame_time()
        self.state.step_accumulator += dt

        if self.state.step_accumulator >= self.state.step_interval:
            self.state.step_accumulator -= self.state.step_interval
            done = self._do_simulation_step()
            if done:
                self.state.is_playing = False

    def _do_simulation_step(self) -> bool:
        """Execute one simulator step and track routed messages.

        Returns True when the simulation is finished (no more events).
        """
        next_time = self.graph.min_next_time(self.simulator.time)
        if not math.isfinite(next_time):
            return True

        # Snapshot connection-level output *before* the step so we can
        # diff afterwards.  For the initial implementation we simply
        # increment message_count per connection by counting outputs.
        #
        # A more precise approach would hook into graph.route(), but
        # this is sufficient for the first iteration.
        done = self.simulator.simulate_step()

        # Increment counts for all connections whose source model was imminent
        # (i.e., produced output this step).
        for conn in self.state.connections:
            model = self.graph.models.get(conn.from_model_id)
            if model is None:
                continue
            if model.time_last_internal_transition == self.simulator.time:
                conn.message_count += 1

        return done

    # ── Drawing ─────────────────────────────────────────────────────

    def _draw(self) -> None:
        rl.begin_drawing()
        rl.clear_background(CANVAS_BG)

        sw = rl.get_screen_width()

        # Canvas content (offset by toolbar + camera)
        rl.begin_scissor_mode(0, TOOLBAR_HEIGHT, sw, rl.get_screen_height() - TOOLBAR_HEIGHT)
        rl.rl_push_matrix()
        rl.rl_translatef(self.state.camera_x, TOOLBAR_HEIGHT + self.state.camera_y, 0)

        # Connections (behind cards)
        for conn in self.state.connections:
            draw_connection(conn, self.state.cards)

        # Cards
        for card in self.state.cards.values():
            model = self.graph.models.get(card.model_id)
            if model is None:
                continue
            selected = (card.model_id == self.state.selected_card)
            draw_card(card, model, selected)

        # Tooltip (in world space so it moves with pan)
        draw_tooltip(self.state.tooltip)

        rl.rl_pop_matrix()
        rl.end_scissor_mode()

        # Toolbar (always on top, screen-space)
        draw_toolbar(sw, self.state.is_playing, self.simulator.time)

        rl.end_drawing()
