from typing import Tuple

from src.devs.AtomicGraph import AtomicGraph
from src.devs.Simulator import Simulator
from src.examples.factories.CapitalProvider import CapitalProvider
from src.examples.factories.Factory import Factory
from src.examples.factories.ProductMarket import ProductMarket


class FactoriesGraph:
    @staticmethod
    def generate_graph() -> Tuple[AtomicGraph, Simulator]:
        graph = AtomicGraph()
        simulator = Simulator(graph)

        capitalMarket = CapitalProvider()
        factory = Factory()
        market = ProductMarket()

        graph.add(capitalMarket)
        graph.add(factory)
        graph.add(market)

        graph.connect(capitalMarket.CAPITAL_OUTPUT_PORT, factory.CAPITAL_INPUT_PORT)
        graph.connect(factory.ITEM_OUTPUT_PORT,market.SELL_ORDER_INPUT_PORT)
        graph.connect(market.MONEY_TRANSFER_OUTPUT_PORT, factory.MONEY_TRANSFER_INPUT_PORT)

        return graph, simulator