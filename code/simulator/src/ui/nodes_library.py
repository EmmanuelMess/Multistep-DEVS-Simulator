import ctypes

from src.ui.blocks import GlobalState


def run_window(resources_path: str, width: int, height: int, global_state: GlobalState):
    nodes_library = ctypes.CDLL('./nodes-gui/lib/libnodes_library.so')
    nodes_library.run_window.argtypes = (ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(GlobalState))
    nodes_library.run_window(resources_path.encode("utf-8"), width, height, ctypes.pointer(global_state))