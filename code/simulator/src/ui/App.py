from dataclasses import dataclass, Field, field

from grandalf.graphs import Graph, Edge, Vertex
from grandalf.layouts import SugiyamaLayout

from src.devs.Simulator import Simulator
from src.devs.Atomic import Atomic
from src.ui import nodes_library
from src.ui.blocks import Port, Connection
import ctypes
from typing import List, Optional, Dict, Tuple

from src.devs.AtomicGraph import AtomicGraph
from src.devs.Types import Id
from src.ui.blocks import GroupBlock, AtomicBlock, GlobalState, Position


class App:
    def __init__(self, graph: AtomicGraph):
        self._global_state = self._parse_graph(graph)
        self._simulator: Optional[Simulator] = None

    def run(self, simulator: Simulator):
        self._simulator = simulator
        nodes_library.run_window("./nodes-gui/lib/resources",800, 450, self._global_state)

    @staticmethod
    def _parse_graph(graph: AtomicGraph) -> GlobalState:
        computed_positions = App._generate_positions(graph)

        group_blocks: List[ctypes.POINTER(GroupBlock)] = []  # pyrefly: ignore

        for i, group in enumerate(graph.groups):
            atomic_blocks: List[ctypes.POINTER(AtomicBlock)] = []  # pyrefly: ignore
            for j, atomic_id in enumerate(group):
                atomic: Atomic = graph.models[atomic_id]

                input_ports: List[ctypes.POINTER(Port)] = []  # pyrefly: ignore
                for input_port in atomic.input_ports:
                    input_ports.append(nodes_library.blocks_create_port(input_port.id, input_port.id))

                output_ports: List[ctypes.POINTER(Port)] = []  # pyrefly: ignore
                for output_port in atomic.output_ports:
                    output_ports.append(nodes_library.blocks_create_port(output_port.id, output_port.id))

                position_x, position_y = computed_positions[atomic_id]

                atomic_block = nodes_library.blocks_create_atomic(
                    atomic_id, atomic.__class__.__name__, input_ports, output_ports,
                    Position( position_x, position_y),
                    400.0, App._compute_height(atomic)
                )

                atomic_blocks.append(atomic_block)

            group_block = nodes_library.blocks_create_group(
                group.id, group.__class__.__name__, atomic_blocks,
                Position( ctypes.c_float(100),  ctypes.c_float(i * 100)),
                250.0, 100.0
            )
            group_blocks.append(group_block)

        free_atomics: List[ctypes.POINTER(AtomicBlock)] = []  # pyrefly: ignore

        for i, (atomic_id, atomic) in enumerate(graph.models.items()):
            if atomic.group_id is not None:
                continue

            input_ports: List[ctypes.POINTER(Port)] = []  # pyrefly: ignore
            for input_port in atomic.input_ports:
                input_ports.append(nodes_library.blocks_create_port(input_port.id, input_port.id))
            output_ports: List[ctypes.POINTER(Port)] = []  # pyrefly: ignore
            for output_port in atomic.output_ports:
                output_ports.append(nodes_library.blocks_create_port(output_port.id, output_port.id))

            position_x, position_y = computed_positions[atomic_id]

            atomic_block = nodes_library.blocks_create_atomic(
                atomic_id, atomic.__class__.__name__, input_ports, output_ports,
                Position( position_x, position_y),
                400.0, App._compute_height(atomic)
            )

            free_atomics.append(atomic_block)

        connections: List[ctypes.POINTER(Connection)] = []  # pyrefly: ignore
        for out_port, in_ports in graph.connections.items():
            for in_port in in_ports:
                connection = nodes_library.blocks_create_connection(out_port.id, in_port.id)
                connections.append(connection)

        global_state = nodes_library.create_global_state(
            Position(ctypes.c_float(0),  ctypes.c_float(0)), group_blocks, free_atomics, connections
        )

        return global_state

    @staticmethod
    def _generate_positions(atomic_graph: AtomicGraph) -> Dict[Id, Tuple[float, float]]:
        @dataclass
        class Box:
            w: float = field()
            h: float = field()
            x: float = field(default=0)
            y: float = field(default=0)

        vertices: Dict[Id, Vertex] = {}
        edges: List[Edge] = []
        boxes: Dict[Id, Box] = {}

        for i, group in enumerate(atomic_graph.groups):
            for j, atomic_id in enumerate(group):
                atomic: Atomic = atomic_graph.models[atomic_id]

                vertices[atomic_id] = Vertex(atomic_id)
                boxes[atomic_id] = Box(400, App._compute_height(atomic))

        for i, (atomic_id, atomic) in enumerate(atomic_graph.models.items()):
            if atomic.group_id is not None:
                continue

            vertices[atomic_id] = Vertex(atomic_id)
            boxes[atomic_id] = Box(400, App._compute_height(atomic))

        for out_port, in_ports in atomic_graph.connections.items():
            for in_port in in_ports:
                edge = Edge(vertices[out_port.atomic_id], vertices[in_port.atomic_id])
                edges.append(edge)

        graph = Graph(vertices.values(), edges)

        for (atomic_id, box) in boxes.items():
            # noinspection PyUnresolvedReferences
            vertices[atomic_id].view = box

        sugiyama = SugiyamaLayout(graph.C[0])  # pass connected components
        sugiyama.init_all()
        sugiyama.draw()

        computed_positions: Dict[Id, Tuple[float, float]] = {}
        for atomic_id, v in vertices.items():
            cx, cy = v.view.xy
            x = cx - v.view.w / 2
            y = cy - v.view.h / 2
            computed_positions[atomic_id] = (x, y)

        return computed_positions

    @staticmethod
    def _compute_height(atomic: Atomic) -> float:
        return 50 + max(len(atomic.input_ports), len(atomic.output_ports)) * 10
