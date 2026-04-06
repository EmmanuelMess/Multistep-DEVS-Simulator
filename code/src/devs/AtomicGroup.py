from typing import Iterator, Set

from deal import ensure

from src.devs.Types import Id


class AtomicGroup:
    def __init__(self, name: str):
        self._name: str = name
        self._atomics: Set[Id] = set()

    def __iter__(self) -> Iterator[Id]:
        return self._atomics.__iter__()

    def __len__(self) -> int:
        return self._atomics.__len__()

    @property
    def name(self):
        return self._name

    @ensure(lambda self, atomic_id, result: atomic_id in self._atomics)
    def add(self, atomic_id: Id):
        self._atomics.add(atomic_id)
