from typing import Iterator, Set

from deal import ensure

from devs.Atomic import Atomic
from src.devs.Types import Id


class AtomicGroup:
    def __init__(self, id: Id, name: str):
        self._id = id
        self._name: str = name
        self._atomics: Set[Id] = set()

    def __iter__(self) -> Iterator[Id]:
        return self._atomics.__iter__()

    def __len__(self) -> int:
        return self._atomics.__len__()

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @ensure(lambda self, atomic, result: atomic.id in self._atomics)
    @ensure(lambda self, atomic, result: atomic.group_id is None,
            message="Remove from the other group before inserting in a new group")
    def add(self, atomic: Atomic):
        self._atomics.add(atomic.id)
        atomic.group = self._id
