from deal import post
import math
from typing import Dict, List, Any, Tuple

from deal import pre, ensure

from src.devs.Atomic import Atomic
from src.devs.Constants import MAX_ATOMICS
from src.devs.Types import Id, Port, Time


class AtomicGraph:
    def __init__(self) -> None:
        self.models: Dict[Id, Atomic] = {}
        self._connections: Dict[Tuple[Id, Port], List[Tuple[Id, Port]]] = {}

        # Input cache to deal with multiple inputs to the same model
        self.models_input_cache: Dict[Id, Dict[Port, List[Any]]] = {}

    @pre(lambda self, model: model.id not in self.models.keys())
    @ensure(lambda self, model, result: len(self.models) <= MAX_ATOMICS)
    def add(self, model: Atomic) -> None:
        self.models[model.id] = model

    @pre(lambda self, output_id, output_port, input_id, input_port:\
                 output_id in self.models.keys() and output_port in self.models[output_id].output_ports, message="Check the output model exists and has port")
    @pre(lambda self, output_id, output_port, input_id, input_port:\
                 input_id in self.models.keys() and input_port in self.models[input_id].input_ports, message="Check the input model exists and has port")
    @pre(lambda self, output_id, output_port, input_id, input_port: output_port[1] is input_port[1], message="Check the type coincides")
    def connect(self, output_id: str, output_port: Port, input_id: str, input_port: Port) -> None:
        if (output_id, output_port) not in self._connections:
            self._connections[output_id, output_port] = []
        self._connections[output_id, output_port].append((input_id, input_port))

    @pre(lambda self, current_time: len(self.models) > 0)
    @pre(lambda self, current_time: math.isfinite(current_time) and 0 <= current_time)
    @ensure(lambda self, current_time, result: current_time <= result)
    def min_next_time(self, current_time: Time) -> Time:
        return min([model.next_internal_time() for model in self.models.values()])

    @pre(lambda self, current_time: math.isfinite(current_time) and 0 <= current_time)
    def get_with_time_advance(self, current_time: Time) -> List[Id]:
        return [model.id for model in self.models.values() if model.next_internal_time() == current_time]

    @pre(lambda self, model_ids, current_time: all([(model_id in self.models) for model_id in model_ids]))
    @pre(lambda self, model_ids, current_time: math.isfinite(current_time) and 0 <= current_time)
    def route(self, model_ids: List[Id], current_time: Time) -> List[Id]:
        """
        Move the outputs for models to input cache for the next model
        :return: Models with input
        """
        for output_model_id in model_ids:
            model = self.models[output_model_id]
            outputs: Dict[Port, List[Any]] = self.models[output_model_id].output()

            for output_port in outputs.keys():
                if len(outputs[output_port]) == 0:
                    continue

                if (output_model_id, output_port) not in self._connections:
                    # The output port doesn't connect to anything
                    continue

                input_ports_ids = self._connections[output_model_id, output_port]
                for input_model_id, input_model_port in input_ports_ids:
                    if input_model_id not in self.models_input_cache:
                        self.models_input_cache[input_model_id] = {}

                    if input_model_port not in self.models_input_cache[input_model_id]:
                        self.models_input_cache[input_model_id][input_model_port] = []

                    self.models_input_cache[input_model_id][input_model_port] += outputs[output_port]

        return list(self.models_input_cache.keys())

    def clear_cache(self) -> None:
        self.models_input_cache = {}