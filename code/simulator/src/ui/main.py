from examples.company.CompanyGraph import CompanyGraph, Mode
from src.ui.App import App


def main():
    graph, simulator = CompanyGraph.generate_graph(Mode.SCRIPTED)

    app = App(graph)
    app.run(simulator)


if __name__ == '__main__':
    main()