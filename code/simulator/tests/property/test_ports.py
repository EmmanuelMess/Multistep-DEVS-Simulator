import math
from dataclasses import dataclass
from random import Random
from typing import Dict, List, Any, Tuple

import hypothesis.strategies as st
from hypothesis import given

from src.devs import Constants
from src.devs.Atomic import Atomic
from src.devs.AtomicGraph import AtomicGraph
from src.devs.IdGenerator import generateId
from src.devs.Simulator import Simulator
from src.devs.Types import Time, Port, Id


@dataclass
class _Message:
    id: Id
    port: Port

def create_atomic_pair(n: int) -> Tuple[Atomic, Atomic]:
    class _SingleStepAtomicOutput(Atomic):
        def __init__(self) -> None:
            super().__init__(generateId("single_step_atomic_output"))
            self.has_run: bool = False
            self.ports = [(i, _Message) for i in range(n)]
            self.set_outports(self.ports)

        def delta_internal(self) -> None:
            self.has_run = True

        def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float) -> None:
            return

        def output(self) -> Dict[Port, List[Any]]:
            return {port: [_Message(generateId("message"), port)] for port in self.ports}

        def time_advance(self) -> Time:
            if not self.has_run:
                return 0.0
            else:
                return float('inf')

    class _SingleStepAtomicInput(Atomic):
        def __init__(self) -> None:
            super().__init__(generateId("single_step_atomic_input"))
            self.has_run: bool = False
            self.ports = [(i, _Message) for i in range(n)]
            self.set_inports(self.ports)

        def delta_internal(self) -> None:
            self.has_run = True

        def delta_external(self, inputs: Dict[Port, List[_Message]], elapsed_time: float) -> None:
            assert len(inputs) == n
            # Ordering shouldn't matter
            for port, messages in inputs.items():
                assert port in self.ports
                for message in messages:
                    assert isinstance(message, _Message)

        def output(self) -> Dict[Port, List[Any]]:
            return {}

        def time_advance(self) -> Time:
            if not self.has_run:
                return 0.0
            else:
                return float('inf')

    return _SingleStepAtomicOutput(), _SingleStepAtomicInput()

@given(n=st.integers(min_value=0, max_value=Constants.MAX_PORTS), r=st.randoms())
def test_time_flow_foward(n, r: Random):
    port_connections = list(range(n))
    r.shuffle(port_connections)

    graph = AtomicGraph()
    simulator = Simulator(graph)

    output, input = create_atomic_pair(n)
    graph.add(output)
    graph.add(input)

    for a_port, b_port in enumerate(port_connections):
        graph.connect(output.id, (a_port, _Message), input.id, (b_port, _Message))

    assert graph.min_next_time(simulator.time) == 0.0

    simulator.simulate_step()

    assert not math.isfinite(graph.min_next_time(simulator.time))