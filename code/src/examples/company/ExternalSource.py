from copy import deepcopy
from typing import List, Any, Dict, Tuple, override

from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Port, Time
from src.examples.company.Messages import (
    Capital, Payment, EmployeeOffering, EmployeeResignation,
    DemandProduct, Product,
)


class ExternalSource(Atomic):
    """
    General-purpose event source for the Company simulation.

    Pre-loaded with a sorted list of (time, port, message) events.
    Fires each batch of same-timestamp events at the correct simulation time.

    Works for both scripted (hand-crafted event list) and random
    (pre-generated from distributions) input modes.
    """

    # All possible output ports — only those with events get connected
    CAPITAL_OUT = (0, Capital)
    PAYMENT_OUT = (1, Payment)
    EMPLOYEE_OFFERING_OUT = (2, EmployeeOffering)
    EMPLOYEE_RESIGNATION_OUT = (3, EmployeeResignation)
    DEMAND_PRODUCT_OUT = (4, DemandProduct)
    PRODUCT_OUT = (5, Product)

    def __init__(self, events: Dict[Time, Tuple[Port, Any]]):
        """
        events: Dict of {Time: (port, message)}, need not be sorted.
        """
        super().__init__(generateId("external_source"))

        self.events: List[Tuple[Time, Tuple[Port, Any]]] = sorted(events.items())
        self.next_index: int = 0
        self.output_buffer: Dict[Port, List[Any]] = {}
        self._next_fire_time: Time = 0.0

        # Register all output ports unconditionally so connections work
        # regardless of which event types are in the list.
        self.set_outports([
            self.CAPITAL_OUT, self.PAYMENT_OUT, self.EMPLOYEE_OFFERING_OUT,
            self.EMPLOYEE_RESIGNATION_OUT, self.DEMAND_PRODUCT_OUT,
            self.PRODUCT_OUT,
        ])

    @override
    def delta_internal(self):
        if self.next_index >= len(self.events):
            return
        target_time, _ = self.events[self.next_index]
        current_messages = filter(lambda e: e[0] == target_time, self.events)

        self.output_buffer = {}
        for _, (port, msg) in current_messages:
            self.output_buffer.setdefault(port, []).append(msg)
            self.next_index += 1

        self._next_fire_time = target_time

    @override
    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float):
        pass  # Source does not receive inputs

    @override
    def output(self) -> Dict[Port, List[Any]]:
        result = deepcopy(self.output_buffer) if self.output_buffer else {}
        for _, messages in result:
            print(f"[OUTSIDE-INPUT] {self.id} Sent {messages}")
        return result

    @override
    def time_advance(self) -> Time:
        if self.next_index >= len(self.events):
            return float('inf')
        if self.time_last_internal_transition is None:
            return self._next_fire_time
        delta = self._next_fire_time - self.time_last_internal_transition
        # Guard against floating-point issues
        return max(delta, 0.0)
