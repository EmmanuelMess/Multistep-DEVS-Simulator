from dataclasses import dataclass
from typing import Type

from src.devs.Types import Id


@dataclass(unsafe_hash=True)
class Port:
    id: Id
    atomic_id: Id
    port_type: Type