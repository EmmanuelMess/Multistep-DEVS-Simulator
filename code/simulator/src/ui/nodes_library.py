import ctypes
from typing import List, Any

from src.devs.Types import Id
from src.ui.blocks import GlobalState, Port, Position, GroupBlock, Connection, AtomicBlock
from src.ui import ctypes_utils
from src.ui.ctypes_utils import array

nodes_library = ctypes.CDLL('./nodes-gui/lib/libnodes_library.so')
c_objects: List[Any] = []
"""
Tracker for all objects used by C 
"""

def blocks_create_port(id: Id, name: str) -> ctypes.POINTER(Port):  # pyrefly: ignore
    # struct Port* blocks_create_port(char* id, char* name)

    global c_objects

    id_c = ctypes.c_char_p(id.encode("utf-8"))
    name_c = ctypes.c_char_p(name.encode("utf-8"))

    c_objects += [id_c, name_c]

    nodes_library.blocks_create_port.restype  = ctypes.POINTER(Port)
    nodes_library.blocks_create_port.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    result = nodes_library.blocks_create_port(
        id_c,
        name_c,
    )
    return result


def blocks_create_atomic(
    id: Id,
    name: str,
    input_ports: List[ctypes.POINTER(Port)],  # pyrefly: ignore
    output_ports: List[ctypes.POINTER(Port)],  # pyrefly: ignore
    position: Position,
    width: float,
    height: float,
) -> ctypes.POINTER(AtomicBlock):  # pyrefly: ignore
    # struct AtomicBlock* blocks_create_atomic(char* id, char* name,
    #     int amount_input_ports, struct Port** input_ports,
    #     int amount_output_ports, struct Port** output_ports,
    #     struct Position position, float width, float height)
    global c_objects

    id_c = ctypes.c_char_p(id.encode("utf-8"))
    name_c = ctypes.c_char_p(name.encode("utf-8"))
    input_ports_c = array(ctypes.POINTER(Port), input_ports)
    output_ports_c = array(ctypes.POINTER(Port), output_ports)

    c_objects += [id_c, name_c, input_ports_c, output_ports_c]

    nodes_library.blocks_create_atomic.restype  = ctypes.POINTER(AtomicBlock)
    nodes_library.blocks_create_atomic.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(Port)),
        ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(Port)),
        Position,
        ctypes.c_float,
        ctypes.c_float,
    ]
    result = nodes_library.blocks_create_atomic(
        id_c,
        name_c,
        ctypes_utils.length(input_ports),
        input_ports_c,
        ctypes_utils.length(output_ports),
        output_ports_c,
        position,
        ctypes.c_float(width),
        ctypes.c_float(height),
    )
    return result


def blocks_create_group(
    id: Id,
    name: str,
    atomics: List[ctypes.POINTER(AtomicBlock)],  # pyrefly: ignore
    position: Position,
    width: float,
    height: float,
) -> ctypes.POINTER(GroupBlock):  # pyrefly: ignore
    # struct GroupBlock* blocks_create_group(char* id, char* name,
    #     int amount_atomics, struct AtomicBlock** atomic_blocks,
    #     struct Position position, float width, float height)
    global c_objects

    id_c = ctypes.c_char_p(id.encode("utf-8"))
    name_c = ctypes.c_char_p(name.encode("utf-8"))
    atomics_c = array(ctypes.POINTER(AtomicBlock), atomics)

    c_objects += [id_c, name_c, atomics_c]

    nodes_library.blocks_create_group.restype  = ctypes.POINTER(GroupBlock)
    nodes_library.blocks_create_group.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(AtomicBlock)),
        Position,
        ctypes.c_float,
        ctypes.c_float,
    ]
    result = nodes_library.blocks_create_group(
        id_c,
        name_c,
        ctypes_utils.length(atomics),
        atomics_c,
        position,
        ctypes.c_float(width),
        ctypes.c_float(height),
    )
    return result


def blocks_create_connection(input_id: Id, output_id: Id) -> ctypes.POINTER(Connection):  # pyrefly: ignore
    # struct Connection* blocks_create_connection(char* input_id, char* output_id)
    global c_objects

    input_id_c = ctypes.c_char_p(input_id.encode("utf-8"))
    output_id_c = ctypes.c_char_p(output_id.encode("utf-8"))

    c_objects += [input_id_c, output_id_c]

    nodes_library.blocks_create_connection.restype  = ctypes.POINTER(Connection)
    nodes_library.blocks_create_connection.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    result = nodes_library.blocks_create_connection(
        input_id_c,
        output_id_c,
    )
    return result


def create_global_state(
    position: Position,
    groups: List[ctypes.POINTER(GroupBlock)],  # pyrefly: ignore
    free_atomics: List[ctypes.POINTER(AtomicBlock)],  # pyrefly: ignore
    connections: List[ctypes.POINTER(Connection)],  # pyrefly: ignore
) -> ctypes.POINTER(GlobalState):  # pyrefly: ignore
    # struct GlobalState* create_global_state(struct Position position,
    #     int amount_groups, struct GroupBlock** group_blocks,
    #     int amount_atomics, struct AtomicBlock** free_atomic_blocks,
    #     int amount_ports, struct Connection** connections)
    global c_objects

    groups_c = array(ctypes.POINTER(GroupBlock), groups)
    free_atomics_c = array(ctypes.POINTER(AtomicBlock), free_atomics)
    connections_c = array(ctypes.POINTER(Connection), connections)

    c_objects += [groups_c, free_atomics_c, connections_c]

    nodes_library.create_global_state.restype  = ctypes.POINTER(GlobalState)
    nodes_library.create_global_state.argtypes = [
        Position,
        ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(GroupBlock)),
        ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(AtomicBlock)),
        ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(Connection)),
    ]
    result = nodes_library.create_global_state(
        position,
        ctypes_utils.length(groups),
        groups_c,
        ctypes_utils.length(free_atomics),
        free_atomics_c,
        ctypes_utils.length(connections),
        connections_c,
    )
    return result

def run_window(resources_path: str, width: int, height: int, global_state: ctypes.POINTER(GlobalState)):  # pyrefly: ignore
    nodes_library.run_window.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(GlobalState)]
    nodes_library.run_window(resources_path.encode("utf-8"), width, height, global_state)
