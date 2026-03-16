from copy import deepcopy
from typing import List, Any, Dict, Optional, cast, override

from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Port, Time
from src.examples.company.Messages import (
    Product, DemandProduct, OfferProduct, AssignEmployee,
    HaltProduction, Improvement, RequestEmployee, Employee,
)


class Manufacturing(Atomic):
    # --- Input ports ---
    DEMAND_PRODUCT_IN = (0, DemandProduct)
    PRODUCT_IN = (1, Product)
    ASSIGN_EMPLOYEE_IN = (2, AssignEmployee)
    HALT_PRODUCTION_IN = (3, HaltProduction)
    IMPROVEMENT_IN = (4, Improvement)

    # --- Output ports ---
    PRODUCT_OUT = (0, Product)
    DEMAND_PRODUCT_OUT = (1, DemandProduct)
    OFFER_PRODUCT_OUT = (2, OfferProduct)
    REQUEST_EMPLOYEE_OUT = (3, RequestEmployee)

    REVIEW_PERIOD = 2.0
    MIN_BASE_TIME = 1.5

    def __init__(
        self,
        bill_of_materials: Dict[str, Dict],
        product_config: Dict[str, Dict],
    ):
        """
        bill_of_materials: {product_type: {"inputs": {input_type: qty}, "base_time": float}}
        product_config: {product_type: {"role": "primary"|"intermediate"|"final", "cost": float}}
        """
        super().__init__(generateId("manufacturing"))

        self.bill_of_materials = bill_of_materials
        self.product_config = product_config

        # Inventory of finished / intermediate goods
        self.inventory: Dict[str, List[Product]] = {}
        # Count of raw / intermediate materials available for production
        self.raw_materials: Dict[str, int] = {}
        # Outstanding demand per product type
        self.demand: Dict[str, int] = {}

        # Employees
        self.assigned_employees: List[Employee] = []
        self.busy_employees: List[Employee] = []

        # Production state
        self.producing: Optional[str] = None
        self.halted: bool = False

        # Efficiency per product (modified by Improvements)
        self.efficiency: Dict[str, float] = {}
        for pt, bom in bill_of_materials.items():
            self.efficiency[pt] = bom["base_time"]

        # Track which raw materials we already requested this cycle
        self._requested_materials: Dict[str, bool] = {}

        # Output buffers
        self._out_products: List[Product] = []
        self._out_demand: List[DemandProduct] = []
        self._out_offer: List[OfferProduct] = []
        self._out_request_emp: List[RequestEmployee] = []

        # Register ports
        for port in [
            self.DEMAND_PRODUCT_IN, self.PRODUCT_IN,
            self.ASSIGN_EMPLOYEE_IN, self.HALT_PRODUCTION_IN,
            self.IMPROVEMENT_IN,
        ]:
            self.set_inport(port)
        for port in [
            self.PRODUCT_OUT, self.DEMAND_PRODUCT_OUT,
            self.OFFER_PRODUCT_OUT, self.REQUEST_EMPLOYEE_OUT,
        ]:
            self.set_outport(port)

    # ------------------------------------------------------------------
    def _has_pending_output(self) -> bool:
        return bool(
            self._out_products or self._out_demand
            or self._out_offer or self._out_request_emp
        )

    def _clear_buffers(self):
        self._out_products.clear()
        self._out_demand.clear()
        self._out_offer.clear()
        self._out_request_emp.clear()
        self._requested_materials.clear()

    def _has_raw_materials(self, product_type: str) -> bool:
        bom = self.bill_of_materials[product_type]
        for input_type, qty in bom["inputs"].items():
            if self.raw_materials.get(input_type, 0) < qty:
                return False
        return True

    def _consume_raw_materials(self, product_type: str):
        bom = self.bill_of_materials[product_type]
        for input_type, qty in bom["inputs"].items():
            self.raw_materials[input_type] -= qty

    def _idle_employees(self) -> List[Employee]:
        return self.assigned_employees

    def _production_time(self, product_type: str) -> float:
        return max(self.efficiency.get(product_type, 5.0), self.MIN_BASE_TIME)

    def _has_demand(self) -> bool:
        return any(d > 0 for d in self.demand.values())

    def _try_start_production(self):
        """Attempt to begin producing a demanded product."""
        if self.producing or self.halted:
            return

        for product_type, demand_count in self.demand.items():
            if demand_count <= 0:
                continue
            if product_type not in self.bill_of_materials:
                continue

            if not self._has_raw_materials(product_type):
                # Request missing raw materials
                bom = self.bill_of_materials[product_type]
                for input_type, qty in bom["inputs"].items():
                    if (self.raw_materials.get(input_type, 0) < qty
                            and not self._requested_materials.get(input_type, False)):
                        self._out_demand.append(
                            DemandProduct(generateId("demand_product"), input_type)
                        )
                        self._requested_materials[input_type] = True
                        print(f"[MFG] {self.id} Requesting raw material {qty}x'{input_type}'")
                continue

            if not self.assigned_employees:
                if not self._out_request_emp:
                    self._out_request_emp.append(
                        RequestEmployee(generateId("req_emp"), self.id)
                    )
                    print(f"[MFG] {self.id} Requesting employee")
                return

            # Start production
            emp = self.assigned_employees.pop(0)
            self.busy_employees.append(emp)
            self._consume_raw_materials(product_type)
            self.producing = product_type
            print(f"[MFG] {self.id} Started producing '{product_type}' "
                  f"(time={self._production_time(product_type):.1f})")
            return

    def _ship_from_inventory(self):
        """Ship inventory items to fulfill outstanding demand."""
        for product_type in list(self.demand.keys()):
            while self.demand.get(product_type, 0) > 0:
                inv = self.inventory.get(product_type, [])
                if not inv:
                    break
                product = inv.pop(0)
                self._out_products.append(product)
                self.demand[product_type] -= 1
                print(f"[MFG] {self.id} Shipped '{product_type}' from inventory")

    def _offer_surplus(self):
        """Offer products in inventory that have no pending demand."""
        offered = set()
        for product_type, products in self.inventory.items():
            if products and self.demand.get(product_type, 0) <= 0 and product_type not in offered:
                self._out_offer.append(
                    OfferProduct(generateId("offer"), product_type)
                )
                offered.add(product_type)

    # ------------------------------------------------------------------
    @override
    def delta_internal(self):
        self._clear_buffers()

        if self.producing:
            # Production complete
            product_type = self.producing
            product = Product(generateId("product"), product_type)
            self.inventory.setdefault(product_type, []).append(product)
            print(f"[INTERNAL] {self.id} Produced {product}")

            # Free the employee
            if self.busy_employees:
                emp = self.busy_employees.pop(0)
                self.assigned_employees.append(emp)

            self.producing = None

        # Ship what we can
        self._ship_from_inventory()

        # Offer surplus
        self._offer_surplus()

        # Try to start next production
        self._try_start_production()

    @override
    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float):
        for port, bag in inputs.items():
            if port == self.DEMAND_PRODUCT_IN:
                for dp in cast(List[DemandProduct], bag):
                    self.demand[dp.product_type] = self.demand.get(dp.product_type, 0) + 1
                    print(f"[INPUT] {self.id} Received {dp}")

            elif port == self.PRODUCT_IN:
                for product in cast(List[Product], bag):
                    self.raw_materials[product.product_type] = (
                        self.raw_materials.get(product.product_type, 0) + 1
                    )
                    print(f"[INPUT] {self.id} Received raw material {product}")

            elif port == self.ASSIGN_EMPLOYEE_IN:
                for assign in cast(List[AssignEmployee], bag):
                    self.assigned_employees.append(assign.employee)
                    if self.halted:
                        self.halted = False
                        print(f"[MFG] {self.id} Resuming production")
                    print(f"[INPUT] {self.id} Received {assign}")

            elif port == self.HALT_PRODUCTION_IN:
                for halt in cast(List[HaltProduction], bag):
                    self.halted = True
                    # Employees taken back by Admin
                    self.assigned_employees.clear()
                    self.busy_employees.clear()
                    if self.producing:
                        print(f"[MFG] {self.id} Production of '{self.producing}' interrupted")
                        self.producing = None
                    print(f"[INPUT] {self.id} Received {halt}")

            elif port == self.IMPROVEMENT_IN:
                for imp in cast(List[Improvement], bag):
                    pt = imp.product_type
                    if pt in self.efficiency:
                        old = self.efficiency[pt]
                        self.efficiency[pt] = max(
                            self.MIN_BASE_TIME,
                            old * (1.0 - imp.efficiency_gain),
                        )
                        print(f"[MFG] {self.id} Improvement for '{pt}': "
                              f"{old:.1f} -> {self.efficiency[pt]:.1f}")

        # Try to start production with new resources
        if not self.producing and not self.halted:
            self._try_start_production()

    @override
    def output(self) -> Dict[Port, List[Any]]:
        result: Dict[Port, List[Any]] = {}
        if self._out_products:
            result[self.PRODUCT_OUT] = deepcopy(self._out_products)
        if self._out_demand:
            result[self.DEMAND_PRODUCT_OUT] = deepcopy(self._out_demand)
        if self._out_offer:
            result[self.OFFER_PRODUCT_OUT] = deepcopy(self._out_offer)
        if self._out_request_emp:
            result[self.REQUEST_EMPLOYEE_OUT] = deepcopy(self._out_request_emp)

        if result:
            print(f"[OUTPUT] {self.id} Sent {result}")
        return result

    @override
    def time_advance(self) -> Time:
        if self.halted and not self._has_pending_output():
            return float('inf')
        if self.producing:
            return self._production_time(self.producing)
        if self._has_pending_output() or self._has_demand():
            return self.REVIEW_PERIOD
        return float('inf')
