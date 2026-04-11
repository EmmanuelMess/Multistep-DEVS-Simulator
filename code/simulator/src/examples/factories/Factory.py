from copy import deepcopy
from typing import List, Any, Dict, cast, override

from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Port
from src.examples.factories.CapitalProvider import Capital
from src.examples.factories.Product import Product
from src.examples.factories.ProductMarket import SellOrder, MoneyTransfer


class Factory(Atomic):
    CAPITAL_INPUT_PORT = (0, Capital)
    MONEY_TRANSFER_INPUT_PORT = (1, MoneyTransfer)
    ITEM_OUTPUT_PORT = (0, SellOrder)

    def __init__(self):
        super().__init__(generateId("factory"))
        self.totalCapital: float = 0
        self.itemCost = 5
        self.period = 1
        self.productForOutput: List[Product] = []

        self.set_inport(self.CAPITAL_INPUT_PORT)
        self.set_inport(self.MONEY_TRANSFER_INPUT_PORT)
        self.set_outport(self.ITEM_OUTPUT_PORT)

    @override
    def delta_internal(self):
        if self.totalCapital < self.itemCost:
            return

        product = Product(generateId("product"))
        self.productForOutput.append(product)

        self.totalCapital -= self.itemCost

        print(f"[INTERNAL] {self.id} Create {product}")

    @override
    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float):
        for (port, inputBag) in inputs.items():
            print(f"[INPUT] {self.id} Received {inputBag}")
            if port == self.CAPITAL_INPUT_PORT:
                for capital in cast(List[Capital], inputBag):
                    self.totalCapital += capital.amount
            elif port == self.MONEY_TRANSFER_INPUT_PORT:
                for payment in cast(List[MoneyTransfer], inputBag):
                    if payment.receiver == self.id:
                        self.totalCapital += payment.amount


    @override
    def output(self) -> Dict[Port, List[Any]]:
        outputBag = []
        for product in self.productForOutput:
            outputBag.append(SellOrder(
                id=generateId("sell_order"), sender=self.id, amount=1, price=self.itemCost+2, productIds=[product.id]
            ))

        self.productForOutput.clear()
        output = {self.ITEM_OUTPUT_PORT: outputBag}

        print(f"[OUTPUT] {self.id} Sent {output}")
        return output

    @override
    def time_advance(self) -> float:
        return self.period if self.totalCapital >= self.itemCost else float('inf')
