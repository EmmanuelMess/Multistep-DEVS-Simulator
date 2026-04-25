import ctypes
import gc

from src.ui.blocks  import Position
from src.ui.nodes_library import blocks_create_port, blocks_create_atomic, blocks_create_group, blocks_create_connection, \
    create_global_state


def test_ffi():
    # Create ports
    p1 = blocks_create_port("port-in-1",  "Input 1")
    p2 = blocks_create_port("port-out-1", "Output 1")

    # Create an atomic block
    atomic = blocks_create_atomic(
        "atomic-1", "My Atomic",
        [p1],
        [p2],
        Position(ctypes.c_float(0),  ctypes.c_float(0)),
        100.0, 60.0,
    )

    # Create a group
    group = blocks_create_group(
        "group-1", "My Group",
        [atomic],
        Position(ctypes.c_float(0),  ctypes.c_float(0)),
        300.0, 200.0,
    )

    # Create a connection
    conn = blocks_create_connection("port-out-1", "port-in-1")

    # Build global state
    state = create_global_state(
        Position(ctypes.c_float(0),  ctypes.c_float(0))
,
        [group],
        [],
        [conn],
    )

    # Check that GC didn't kill p1's pointers
    gc.collect()
    assert p1.contents.id == b"port-in-1"
    assert p1.contents.name == b"Input 1"
    assert p2.contents.id == b"port-out-1"
    assert p2.contents.name == b"Output 1"

    assert state.contents.amount_groups == 1
    assert state.contents.amount_atomics == 0
    assert state.contents.amount_connections == 1
