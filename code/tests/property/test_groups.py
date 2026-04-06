from typing import Dict, List, Any

from hypothesis import given, reproduce_failure
import hypothesis.strategies as st

from src.devs import Constants
from src.devs.Atomic import Atomic
from src.devs.AtomicGraph import AtomicGraph
from src.devs.IdGenerator import generateId
from src.devs.Simulator import Simulator
from src.devs.Types import Port, Time


class _SingleStepAtomic(Atomic):
    def __init__(self) -> None:
        super().__init__(generateId("single_step_atomic"))
        self.has_run: bool = False

    def delta_internal(self) -> None:
        self.has_run = True

    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float) -> None:
        return

    def output(self) -> Dict[Port, List[Any]]:
        return {}

    def time_advance(self) -> Time:
        if not self.has_run:
            return 0.0
        else:
            return float('inf')

@given(n=st.integers(min_value=1, max_value=Constants.MAX_ATOMICS))
def test_singles_in_groups(n):
    graph = AtomicGraph()
    simulator = Simulator(graph)

    for i in range(n):
        atomic = _SingleStepAtomic()
        group = graph.groups.add_group(generateId("group"), f"group {i}")

        graph.add(atomic)
        group.add(atomic.id)

    assert len(graph.groups) == n

    for group in graph.groups:
        assert len(group) == 1

    simulator.simulate_step()

    assert len(graph.groups) == n

    for group in graph.groups:
        assert len(group) == 1