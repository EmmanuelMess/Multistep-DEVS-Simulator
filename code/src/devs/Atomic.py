from abc import ABCMeta, abstractmethod
from math import isfinite
from typing import Dict, Optional, List, Any

from deal import pre, ensure, post, pure

from src.devs.Types import Id, Port


class Atomic(metaclass=ABCMeta):
    def __init__(self, id: Id):
        self.input_ports: List[Port] = []
        self.output_ports: List[Port] = []
        self.id = id
        self.time_last_internal_transition: Optional[float] = None

    @abstractmethod
    def delta_internal(self):
        pass

    @abstractmethod
    @pre(lambda self, inputs, elapsed_time: all([port in self.input_ports for port in inputs.keys()]))
    @pre(lambda self, inputs, elapsed_time: all([all([isinstance(input_val, type_) for input_val in inputs[(port_id, type_)]]) for (port_id, type_) in inputs.keys()]))
    @pre(lambda self, inputs, elapsed_time: isfinite(elapsed_time) and 0 <= elapsed_time < self.time_advance())
    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float):
        pass

    @pre(lambda self, inputs: all([port in self.input_ports for port in inputs.keys()]))
    @pre(lambda self, inputs: all([all([isinstance(input_val, type_) for input_val in inputs[(port_id, type_)]]) for (port_id, type_) in inputs.keys()]))
    def delta_confluence(self, inputs: Dict[Port, List[Any]]):
        self.delta_external(inputs, 0)
        self.delta_internal()

    @abstractmethod
    @ensure(lambda self, result: all([port in self.output_ports for port in result.keys()]))
    @pre(lambda self, result: all([all([isinstance(input_val, type_) for input_val in result[(port_id, type_)]]) for (port_id, type_) in result.keys()]))
    def output(self) -> Dict[Port, List[Any]]:
        pass

    @abstractmethod
    @post(lambda output: output >= 0)
    @pure
    def time_advance(self) -> float:
        pass

    def next_internal_time(self) -> float:
        if self.time_last_internal_transition is None:
            # The transition never happened, so start at 0 + ta()
            return self.time_advance()

        return self.time_last_internal_transition + self.time_advance()

    def set_inport(self, port: Port):
        self.input_ports.append(port)

    def set_outport(self, port: Port):
        self.output_ports.append(port)