import ctypes
from typing import Union


class ClipArea(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("width", ctypes.c_float),
        ("height", ctypes.c_float),
    ]

class Position(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]

class Port(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
    ]

class AtomicBlock(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("name", ctypes.c_char_p),
        ("amount_input_ports", ctypes.c_int),
        ("input_ports", ctypes.POINTER(Port)),
        ("amount_output_ports", ctypes.c_int),
        ("output_ports", ctypes.POINTER(Port)),
        ("position", Position),
        ("width", ctypes.c_float),
        ("height", ctypes.c_float),
    ]

class GroupBlock(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("name", ctypes.c_char_p),
        ("amount_atomics", ctypes.c_int),
        ("atomics", ctypes.POINTER(AtomicBlock)),
        ("position", Position),
        ("width", ctypes.c_float),
        ("height", ctypes.c_float),
    ]

Block = Union[AtomicBlock, GroupBlock]

class GlobalState(ctypes.Structure):
    _fields_ = [
        ("position", Position),
        ("amount_groups", ctypes.c_int),
        ("groups", ctypes.POINTER(GroupBlock)),
        ("amount_atomics", ctypes.c_int),
        ("atomics", ctypes.POINTER(AtomicBlock)),
    ]