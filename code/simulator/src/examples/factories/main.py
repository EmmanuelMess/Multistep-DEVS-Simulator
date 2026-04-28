import math

from examples.factories.FactoriesGraph import FactoriesGraph


def main():
    graph, simulator = FactoriesGraph.generate_graph()

    next_time = graph.min_next_time(simulator.time)
    while math.isfinite(next_time):
        print(f"== Time {next_time} ==")

        simulator.simulate_step()

        next_time = graph.min_next_time(simulator.time)

if __name__ == '__main__':
    main()