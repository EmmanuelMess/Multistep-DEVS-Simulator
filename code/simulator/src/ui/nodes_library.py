import ctypes

from src.ui.blocks import GlobalState


def run_window(width: int, height: int, global_state: GlobalState):
    nodes_library = ctypes.CDLL('./libnodes_library.so')
    nodes_library.run_window.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.POINTER(GlobalState))
    nodes_library.run_window(width, height, ctypes.pointer(global_state))