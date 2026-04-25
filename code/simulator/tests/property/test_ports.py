import math
from dataclasses import dataclass
from random import Random
from typing import Dict, List, Any, Tuple

import hypothesis.strategies as st
from hypothesis import given

from src.devs.Port import Port
from src.devs import Constants
from src.devs.Atomic import Atomic
from src.devs.AtomicGraph import AtomicGraph
from src.devs.IdGenerator import generateId
from src.devs.Simulator import Simulator
from src.devs.Types import Time, Id


@dataclass
class _Message:
    id: Id
    port: Port

def create_atomic_pair(n: int, output_id: Id, output_ports: List[Port], input_id: Id, input_ports: List[Port]) -> Tuple[Atomic, Atomic]:
    class _SingleStepAtomicOutput(Atomic):
        def __init__(self) -> None:
            super().__init__(output_id)
            self.has_run: bool = False
            self.ports = output_ports
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
            super().__init__(input_id)
            self.has_run: bool = False
            self.ports = input_ports
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
    output_id = generateId("single_step_atomic_output")
    ports_output = [Port(generateId("single_step_atomic_output_port"), output_id, _Message) for _ in range(n)]
    input_id = generateId("single_step_atomic_input")
    ports_input = [Port(generateId("single_step_atomic_input_port"), input_id, _Message) for _ in range(n)]

    # Shuffle everything
    r.shuffle(ports_output)

    port_connections = zip(ports_output, ports_input)

    graph = AtomicGraph()
    simulator = Simulator(graph)

    output, input = create_atomic_pair(n, output_id, ports_output, input_id, ports_input)
    graph.add(output)
    graph.add(input)

    for out_port, in_port in port_connections:
        graph.connect(out_port, in_port)

    assert graph.min_next_time(simulator.time) == 0.0

    simulator.simulate_step()

    assert not math.isfinite(graph.min_next_time(simulator.time))