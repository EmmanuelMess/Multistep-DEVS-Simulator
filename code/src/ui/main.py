"""Entry point for launching the DEVS simulator UI.

Usage from Python::

    from src.ui.main import launch
    launch(graph, simulator)

Or run directly to demo with the company example::

    python -m src.ui.main          # scripted mode (default)
    python -m src.ui.main random   # random mode
"""

import sys

from src.devs.AtomicGraph import AtomicGraph
from src.devs.Simulator import Simulator
from src.ui.app import App


def launch(graph: AtomicGraph, simulator: Simulator) -> None:
    """Open the UI window for an already-wired graph and simulator."""
    app = App(graph, simulator)
    app.run()


def _demo() -> None:
    """Boot the company example and launch the UI."""
    from src.examples.company.main import build_graph, generate_scripted_events, generate_random_events

    mode = sys.argv[1] if len(sys.argv) > 1 else "scripted"
    if mode == "random":
        events = generate_random_events()
    else:
        events = generate_scripted_events()

    graph, simulator = build_graph(events)
    launch(graph, simulator)


if __name__ == "__main__":
    _demo()
