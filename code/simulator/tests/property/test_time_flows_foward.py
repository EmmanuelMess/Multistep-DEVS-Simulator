from hypothesis import given, reproduce_failure
import hypothesis.strategies as st

import math

from src.devs import Constants
from src.devs.AtomicGraph import AtomicGraph
from src.devs.IdGenerator import generateId
from typing import Dict, List, Any

from src.devs.Atomic import Atomic
from src.devs.Simulator import Simulator
from src.devs.Types import Time, Port

def create_atomic(t: float)-> Atomic:
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
                return t
            else:
                return float('inf')

    return _SingleStepAtomic()

@given(times=st.lists(st.floats(min_value=0.0), min_size=1, max_size=Constants.MAX_ATOMICS))
def test_time_flow_foward(times):
    graph = AtomicGraph()
    simulator = Simulator(graph)

    for t in times:
        graph.add(create_atomic(t))

    # Merge all equal times, and sort them to validate time flow
    for t in sorted(set(times)):
        assert graph.min_next_time(simulator.time) == t

        simulator.simulate_step()

    assert not math.isfinite(graph.min_next_time(simulator.time))