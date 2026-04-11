import sys
from math import inf
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import List, override, Union, Dict, Any, cast

import deal
from deal import inv

from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Id, Port
from src.examples.factories.CapitalProvider import Capital

@dataclass
class BuyOrder:
    id: Id
    sender: Id
    amount: int
    price: float

#@inv(lambda obj: obj.amount == len(obj.productIds))
@dataclass
class SellOrder:
    id: Id
    sender: Id
    amount: int
    price: float
    productIds: List[Id]

Order = Union[BuyOrder, SellOrder]

@dataclass
class GoodsTransfer:
    id: Id
    receiver: Id
    containedGoods: List[Id]

@dataclass
class MoneyTransfer:
    id: Id
    receiver: Id
    amount: float

Transfer = Union[GoodsTransfer, MoneyTransfer]


class ProductMarket(Atomic):
    SELL_ORDER_INPUT_PORT = (0, SellOrder)
    BUY_ORDER_INPUT_PORT = (1, BuyOrder)
    GOODS_TRANSFER_OUTPUT_PORT = (0, GoodsTransfer)
    MONEY_TRANSFER_OUTPUT_PORT = (1, MoneyTransfer)

    def __init__(self):
        super().__init__(generateId("product_market"))
        self.buyOrders: List[BuyOrder] = []
        self.sellOrders: List[SellOrder] = []

        self.transfers: List[Transfer] = []

        self.set_inport(self.SELL_ORDER_INPUT_PORT)
        self.set_inport(self.BUY_ORDER_INPUT_PORT)
        self.set_outport(self.GOODS_TRANSFER_OUTPUT_PORT)
        self.set_outport(self.MONEY_TRANSFER_OUTPUT_PORT)

    @override
    def delta_internal(self):
        self.buyOrders.sort(key=lambda order: (-order.price, order.amount))
        self.sellOrders.sort(key=lambda order: (order.price, order.amount))

        print(f"Buy orders: {[(order.price, order.amount) for order in self.buyOrders]} "
              f"Sell orders: {[(order.price, order.amount) for order in self.sellOrders]}")

        if self.buyOrders[0].price < self.sellOrders[0].price:
            return

        for aOrders, bOrders in [(self.buyOrders, self.sellOrders), (self.sellOrders, self.buyOrders)]:
            for aOrder in aOrders:
                # orders at price
                bOrdersAtPrice = [order for order in bOrders if order.price == aOrder.price]
                bOrdersAtPrice.sort(key=lambda order: order.amount)
                total = 0
                lastIndex = 0
                for i, sellOrder in enumerate(bOrdersAtPrice):
                    if total + sellOrder.amount > aOrder.amount:
                        break

                    lastIndex = i
                    total += sellOrder.amount

                if total == aOrder.amount:
                    # TODO

                    print(f"[INTERNAL] {self.id} Create trades {aOrder.id} <-> {[order.id for order in bOrdersAtPrice[:lastIndex+1]]}")


    @override
    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float):
        for port, bag in inputs.items():
            for order in bag:
                print(f"[INPUT] {self.id} Received {order}")

                order = cast(Order, order)

                if isinstance(order, BuyOrder):
                    self.buyOrders.append(order)
                elif isinstance(order, SellOrder):
                    self.sellOrders.append(order)
                else:
                    print(f"Error: undefined order type {order}")
                    exit(1)

    @override
    def output(self) -> Dict[Port, List[Any]]:
        print(f"[OUTPUT] {self.id} Sent {{}}")
        return {}

    @override
    def time_advance(self) -> float:
        if len(self.transfers) > 0:
            return sys.float_info.epsilon

        return inf

