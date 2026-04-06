from deal import ensure
from typing import Dict, Iterator

from deal import pre

from src.devs.AtomicGroup import AtomicGroup
from src.devs.Types import Id


class AtomicGroups:
    def __init__(self):
        self._groups: Dict[Id, AtomicGroup] = {}

    def __iter__(self) -> Iterator[AtomicGroup]:
        return self._groups.values().__iter__()

    def __len__(self) -> int:
        return self._groups.__len__()

    @ensure(lambda self, group_id, _, result: group_id in self._groups.keys())
    def add_group(self, group_id: Id, name: str) -> AtomicGroup:
        self._groups[group_id] = AtomicGroup(name)
        return self._groups[group_id]

    @pre(lambda self, group_id: group_id in self._groups.keys())
    def find_group(self, group_id: Id) -> AtomicGroup:
        return self._groups[group_id]
