from src.ui import nodes_library, ctypes_utils
from src.ui.blocks import ClipArea, Port
import ctypes
from typing import List

from src.devs.AtomicGraph import AtomicGraph
from src.devs.Types import Id
from src.ui.blocks import GroupBlock, AtomicBlock, GlobalState, Position


class App:
    def __init__(self, graph: AtomicGraph):
        self.global_state = self._parse_graph(graph)

    def run(self):
        state = self.global_state
        nodes_library.run_window("./nodes-gui/lib/resources",800, 450, state)

    def _parse_graph(self, graph: AtomicGraph) -> GlobalState:
        groups: List[GroupBlock] = []
        free_blocks: List[AtomicBlock] = []

        atomics_in_groups: List[Id] = []
        for group in graph.groups:
            atomics_in_group: List[Id] = [atomic_id for atomic_id in group]

            atomic_blocks: List[AtomicBlock] = []
            for i, id in enumerate(group):
                input_ports: List[Port] = [Port("Intermediates".encode('utf-8')), Port("Messages".encode('utf-8'))]
                output_ports: List[Port] = [Port("Production".encode('utf-8')), Port("Messages".encode('utf-8'))]

                block = AtomicBlock(
                    0, "Manufacturing".encode('utf-8'),
                    ctypes_utils.length(input_ports), ctypes_utils.array(Port, input_ports),
                    ctypes_utils.length(output_ports), ctypes_utils.array(Port, output_ports),
                    ClipArea( ctypes.c_float(0),  ctypes.c_float(0),  ctypes.c_float(100),  ctypes.c_float(100))
                )

                atomic_blocks.append(block)

            rect = ClipArea( ctypes.c_float(0),  ctypes.c_float(0),  ctypes.c_float(100),  ctypes.c_float(100))
            block = GroupBlock(
                0, "Company".encode('utf-8'),
                ctypes_utils.length(atomic_blocks), ctypes_utils.array(AtomicBlock, atomic_blocks),
                rect
            )
            groups.append(block)
            atomics_in_groups += atomics_in_group

        for atomic in graph.models.keys():
            if atomic not in atomics_in_groups:
                input_ports: List[Port] = [Port("Intermediates".encode('utf-8')), Port("Messages".encode('utf-8'))]
                output_ports: List[Port] = [Port("Production".encode('utf-8')), Port("Messages".encode('utf-8'))]

                block = AtomicBlock(
                    0, "Manufacturing".encode('utf-8'),
                    ctypes_utils.length(input_ports), ctypes_utils.array(Port, input_ports),
                    ctypes_utils.length(output_ports), ctypes_utils.array(Port, output_ports),
                    ClipArea( ctypes.c_float(0),  ctypes.c_float(0),  ctypes.c_float(100),  ctypes.c_float(100))
                )

                free_blocks.append(block)

        global_state = GlobalState(
            Position(0, 0),
            ctypes_utils.length(groups), ctypes_utils.array(GroupBlock, groups),
            ctypes_utils.length(free_blocks), ctypes_utils.array(AtomicBlock, free_blocks)
        )

        return global_state