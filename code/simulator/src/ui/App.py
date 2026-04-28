from src.devs.Simulator import Simulator
from src.devs.Atomic import Atomic
from src.ui import nodes_library
from src.ui.blocks import Port, Connection
import ctypes
from typing import List, Optional

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
        group_blocks: List[ctypes.POINTER(GroupBlock)] = []  # pyrefly: ignore

        atomics_in_groups: List[Id] = []
        for i, group in enumerate(graph.groups):
            atomics_in_group: List[Id] = [atomic_id for atomic_id in group]

            atomic_blocks: List[ctypes.POINTER(AtomicBlock)] = []  # pyrefly: ignore
            for j, atomic_id in enumerate(group):
                atomic: Atomic = graph.models[atomic_id]

                input_ports: List[ctypes.POINTER(Port)] = []  # pyrefly: ignore
                for input_port in atomic.input_ports:
                    input_ports.append(nodes_library.blocks_create_port(input_port.id, input_port.id))

                output_ports: List[ctypes.POINTER(Port)] = []  # pyrefly: ignore
                for output_port in atomic.output_ports:
                    output_ports.append(nodes_library.blocks_create_port(output_port.id, output_port.id))

                atomic_block = nodes_library.blocks_create_atomic(
                    atomic_id, atomic.__class__.__name__, input_ports, output_ports,
                    Position( ctypes.c_float(0),  ctypes.c_float(j * 100)),
                    400.0, 100.0
                )

                atomic_blocks.append(atomic_block)

            group_block = nodes_library.blocks_create_group(
                group.id, group.__class__.__name__, atomic_blocks,
                Position( ctypes.c_float(100),  ctypes.c_float(i * 100)),
                250.0, 100.0
            )
            group_blocks.append(group_block)
            atomics_in_groups += atomics_in_group

        free_atomics: List[ctypes.POINTER(AtomicBlock)] = []  # pyrefly: ignore

        for i, (atomic_id, atomic) in enumerate(graph.models.items()):
            if atomic_id in atomics_in_groups:
                continue

            input_ports: List[ctypes.POINTER(Port)] = []  # pyrefly: ignore
            for input_port in atomic.input_ports:
                input_ports.append(nodes_library.blocks_create_port(input_port.id, input_port.id))
            output_ports: List[ctypes.POINTER(Port)] = []  # pyrefly: ignore
            for output_port in atomic.output_ports:
                output_ports.append(nodes_library.blocks_create_port(output_port.id, output_port.id))

            atomic_block = nodes_library.blocks_create_atomic(
                atomic_id, atomic.__class__.__name__, input_ports, output_ports,
                Position( ctypes.c_float(-300),  ctypes.c_float(i * 100)),
                400.0, 100.0
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
