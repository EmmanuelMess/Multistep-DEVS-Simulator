import math
import sys

from src.examples.company.CompanyGraph import Mode, CompanyGraph


def main(mode_string: str = "scripted"):
    if mode_string == "scripted":
        mode = Mode.SCRIPTED
    elif mode_string == "random":
        mode = Mode.RANDOM
    else:
        raise ValueError(f"Unknown mode: {mode_string}")

    graph, simulator = CompanyGraph.generate_graph(mode)

    print(f"=== Company Simulation ({mode} mode) ===\n")

    next_time = graph.min_next_time(simulator.time)
    while math.isfinite(next_time):
        print(f"\n== Time {next_time} ==")
        simulator.simulate_step()
        next_time = graph.min_next_time(simulator.time)

    print("\n=== Simulation complete ===")


if __name__ == '__main__':
    main(sys.argv[1])
