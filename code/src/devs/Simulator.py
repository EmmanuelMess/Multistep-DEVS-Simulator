import math
from typing import List

from src.devs.AtomicGraph import AtomicGraph
from src.devs.Constants import MAX_ITERATIONS
from src.devs.Types import Id


class Simulator:
    def __init__(self, graph: AtomicGraph) -> None:
        self.graph = graph
        self.time = 0

    def simulate(self) -> None:
        next_time = self.graph.min_next_time(self.time)
        while math.isfinite(next_time):
            self.simulate_step()

            next_time = self.graph.min_next_time(self.time)

    def simulate_step(self) -> bool:
        """
        Simulate a single step
        :return: True if the simulation has no more steps
        """
        current_time = self.graph.min_next_time(self.time)
        if current_time == math.inf:
            # Simulation already ended
            return True

        already_run_models: List[Id] = []

        for i in range(MAX_ITERATIONS):
            imminent_model_ids = self.graph.get_with_time_advance(current_time) # TODO optimize
            with_input_model_ids = self.graph.route(imminent_model_ids, current_time)
            # TODO start by processing only imminents, then process the inputs
            # TODO check which imminents should be processed on the first run

            if len(imminent_model_ids) == 0 and len(with_input_model_ids) == 0:
                break

            # TODO use getters from graph?
            for model_id in (imminent_model_ids + with_input_model_ids):
                if model_id in already_run_models:
                    print(f"Error: model {model_id} is being run twice at instant {current_time}")
                    exit(1)

                model = self.graph.models[model_id]

                is_imminent = model_id in imminent_model_ids
                has_input = model_id in with_input_model_ids

                assert ((is_imminent and not has_input)
                        or (is_imminent and has_input)
                        or (not is_imminent and has_input))

                if is_imminent and not has_input:
                    model.delta_internal()
                elif is_imminent and has_input:
                    model.delta_confluence(self.graph.models_input_cache[model_id])
                elif not is_imminent and has_input:
                    elapsed = current_time - model.time_last_internal_transition if model.time_last_internal_transition is not None else current_time
                    model.delta_external(self.graph.models_input_cache[model_id], elapsed)

                model.time_last_internal_transition = current_time
                already_run_models.append(model_id)

            self.graph.clear_cache()

        self.time = current_time

        return False
