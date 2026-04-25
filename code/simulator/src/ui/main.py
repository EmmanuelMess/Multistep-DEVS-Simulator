from src.devs.AtomicGraph import AtomicGraph
from src.devs.AtomicGroup import AtomicGroup
from src.devs.IdGenerator import generateId
from src.examples.factories.CapitalProvider import CapitalProvider
from src.examples.factories.Factory import Factory
from src.examples.factories.ProductMarket import ProductMarket
from src.ui.App import App


def main():
    capitalMarket = CapitalProvider()
    factory = Factory()
    market = ProductMarket()

    group = AtomicGroup(generateId("group"), "group")
    group.add(factory.id)

    graph = AtomicGraph()
    graph.add_all([capitalMarket, factory, market])
    graph.groups.add_group(group)

    graph.connect(capitalMarket.CAPITAL_OUTPUT_PORT, factory.CAPITAL_INPUT_PORT)
    graph.connect(factory.ITEM_OUTPUT_PORT,market.SELL_ORDER_INPUT_PORT)
    graph.connect(market.MONEY_TRANSFER_OUTPUT_PORT, factory.MONEY_TRANSFER_INPUT_PORT)

    app = App(graph)
    app.run()


if __name__ == '__main__':
    main()