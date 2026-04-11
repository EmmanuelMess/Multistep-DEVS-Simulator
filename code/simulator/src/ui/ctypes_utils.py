import ctypes
from typing import List, TypeVar

T = TypeVar("T")
def length(l: List[T]) -> ctypes.c_int:
    return ctypes.c_int(len(l))

def array(t: type[T], l: List[T]): # -> ctypes.POINTER(t):  # pyrefly: ignore
    return (t * len(l))(*l)  # pyrefly: ignore