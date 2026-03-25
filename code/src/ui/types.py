"""Data types for the UI state."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.devs.Types import Port, Id


@dataclass
class PortInfo:
    """Displayable information about a single port."""
    port: Port
    name: str
    is_input: bool


@dataclass
class CardState:
    """Visual state for one atomic model card on the canvas."""
    model_id: Id
    display_name: str
    x: float
    y: float
    width: float = 240.0
    height: float = 0.0          # computed from port count
    input_ports: List[PortInfo] = field(default_factory=list)
    output_ports: List[PortInfo] = field(default_factory=list)
    is_dragging: bool = False
    drag_offset_x: float = 0.0
    drag_offset_y: float = 0.0


@dataclass
class ConnectionInfo:
    """One directed connection between an output port and an input port."""
    from_model_id: Id
    from_port: Port
    from_port_index: int
    to_model_id: Id
    to_port: Port
    to_port_index: int
    message_count: int = 0       # cumulative messages routed
    pair_index: int = 0          # index among connections with same (from, to) models
    pair_count: int = 1          # total connections between the same model pair


@dataclass
class MessageStat:
    """One row in the message-inspector tooltip."""
    type_name: str
    count: int = 0


@dataclass
class TooltipState:
    """State of the connection tooltip popup."""
    visible: bool = False
    x: float = 0.0
    y: float = 0.0
    connection_idx: int = -1
    stats: List[MessageStat] = field(default_factory=list)


@dataclass
class AppState:
    """Top-level mutable UI state."""
    cards: Dict[Id, CardState] = field(default_factory=dict)
    connections: List[ConnectionInfo] = field(default_factory=list)

    # Simulation control
    is_playing: bool = False
    step_interval: float = 0.5   # seconds between sim steps when playing
    step_accumulator: float = 0.0

    # Selection / interaction
    selected_card: Optional[Id] = None
    tooltip: TooltipState = field(default_factory=TooltipState)

    # Camera (canvas panning)
    camera_x: float = 0.0
    camera_y: float = 0.0
    is_panning: bool = False
    pan_start_x: float = 0.0
    pan_start_y: float = 0.0
