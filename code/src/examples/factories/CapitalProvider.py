from copy import deepcopy
from dataclasses import dataclass
from typing import List, Any, Dict, cast, override

from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Port


@dataclass
class Capital:
    id: str
    amount: float

class CapitalProvider(Atomic):
    CAPITAL_OUTPUT_PORT = (0, Capital)

    def __init__(self):
        super().__init__(generateId("capital_provider"))
        self.totalCapital = 100
        self.assigment = 2
        self.period = 2
        self.capital: List[Capital] = []

        self.set_outport(self.CAPITAL_OUTPUT_PORT)

    @override
    def delta_internal(self):
        if self.totalCapital < self.assigment:
            return

        capital = Capital(generateId("capital"), self.assigment)
        self.capital.append(capital)

        self.totalCapital -= self.assigment

        print(f"[INTERNAL] {self.id} Create {capital}")

    @override
    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float):
        for input in inputs:
            print(f"[INPUT] {self.id} Received {input}")

    @override
    def output(self) -> Dict[Port, List[Any]]:
        output = {self.CAPITAL_OUTPUT_PORT: deepcopy(self.capital)}
        self.capital.clear()

        print(f"[OUTPUT] {self.id} Sent {output}")
        return output

    @override
    def time_advance(self) -> float:
        if self.totalCapital >= self.assigment:
            return self.period

        return float('inf')

