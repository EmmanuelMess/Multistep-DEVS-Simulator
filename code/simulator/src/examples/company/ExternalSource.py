from copy import deepcopy
from typing import List, Any, Dict, Tuple, override, Callable

from src.devs.Port import Port
from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Time
from src.examples.company.Messages import (
    Capital, Payment, EmployeeOffering, EmployeeResignation,
    DemandProduct, Product, OfferProduct,
)


class ExternalSource(Atomic):
    """
    General-purpose event source for the Company simulation.

    Pre-loaded with a sorted list of (time, port, message) events.
    Fires each batch of same-timestamp events at the correct simulation time.

    Works for both scripted (hand-crafted event list) and random
    (pre-generated from distributions) input modes.
    """

    def __init__(self, generate_events: Callable[["ExternalSource"], Dict[Time, List[Tuple[Port, Any]]]]):
        """
        events: Dict of {Time: [(port, message), ...]}, need not be sorted.
        Multiple events at the same timestamp are supported.
        """
        super().__init__(generateId("external_source"))

        # All possible output ports — only those with events get connected
        self.CAPITAL_OUT = Port(generateId("external_source_port"), self.id, Capital)
        self.PAYMENT_OUT = Port(generateId("external_source_port"), self.id, Payment)
        self.EMPLOYEE_OFFERING_OUT = Port(generateId("external_source_port"), self.id, EmployeeOffering)
        self.EMPLOYEE_RESIGNATION_OUT = Port(generateId("external_source_port"), self.id, EmployeeResignation)
        self.DEMAND_PRODUCT_OUT = Port(generateId("external_source_port"), self.id, DemandProduct)
        self.PRODUCT_OUT = Port(generateId("external_source_port"), self.id, Product)
        self.OFFER_PRODUCT_OUT = Port(generateId("external_source_port"), self.id, OfferProduct)

        events: Dict[Time, List[Tuple[Port, Any]]] = generate_events(self)

        # Flatten into sorted list of (time, (port, msg))
        flat: List[Tuple[Time, Tuple[Port, Any]]] = []
        for t, event_list in events.items():
            for event in event_list:
                flat.append((t, event))
        flat.sort(key=lambda e: e[0])

        self.events = flat
        self.next_index: int = 0
        self.output_buffer: Dict[Port, List[Any]] = {}
        self._next_fire_time: Time = 0.0

        # Register all output ports unconditionally so connections work
        # regardless of which event types are in the list.
        self.set_outports([
            self.CAPITAL_OUT, self.PAYMENT_OUT, self.EMPLOYEE_OFFERING_OUT,
            self.EMPLOYEE_RESIGNATION_OUT, self.DEMAND_PRODUCT_OUT,
            self.PRODUCT_OUT, self.OFFER_PRODUCT_OUT,
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
        for _, messages in result.items():
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
