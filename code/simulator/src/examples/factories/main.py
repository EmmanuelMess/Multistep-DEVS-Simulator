import math

from src.devs.AtomicGraph import AtomicGraph
from src.devs.Simulator import Simulator
from src.examples.factories.CapitalProvider import CapitalProvider
from src.examples.factories.Factory import Factory
from src.examples.factories.ProductMarket import ProductMarket


def main():
    graph = AtomicGraph()
    simulator = Simulator(graph)

    capitalMarket = CapitalProvider()
    factory = Factory()
    market = ProductMarket()

    graph.add(capitalMarket)
    graph.add(factory)
    graph.add(market)

    graph.connect(capitalMarket.id, capitalMarket.CAPITAL_OUTPUT_PORT, factory.id, factory.CAPITAL_INPUT_PORT)
    graph.connect(factory.id, factory.ITEM_OUTPUT_PORT, market.id, market.SELL_ORDER_INPUT_PORT)
    graph.connect(market.id, market.MONEY_TRANSFER_OUTPUT_PORT, factory.id, factory.MONEY_TRANSFER_INPUT_PORT)

    next_time = graph.min_next_time(simulator.time)
    while math.isfinite(next_time):
        print(f"== Time {next_time} ==")

        simulator.simulate_step()

        next_time = graph.min_next_time(simulator.time)

if __name__ == '__main__':
    main()