from copy import deepcopy
from typing import List, Any, Dict, cast, override

from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Port, Time
from src.examples.company.Messages import (
    Capital, Payment, EmployeeOffering, EmployeeResignation,
    RequestEmployee, ImprovementsCost, AssignEmployee,
    HaltProduction, StartImprovements, LookingForEmployee,
    FireEmployee, Employee,
)


class Administration(Atomic):
    # --- Input ports ---
    CAPITAL_IN = (0, Capital)
    PAYMENT_IN = (1, Payment)
    EMPLOYEE_OFFERING_IN = (2, EmployeeOffering)
    EMPLOYEE_RESIGNATION_IN = (3, EmployeeResignation)
    REQUEST_EMPLOYEE_IN = (4, RequestEmployee)
    IMPROVEMENTS_COST_IN = (5, ImprovementsCost)

    # --- Output ports ---
    ASSIGN_EMPLOYEE_MFG_OUT = (0, AssignEmployee)
    ASSIGN_EMPLOYEE_RD_OUT = (1, AssignEmployee)
    HALT_PRODUCTION_OUT = (2, HaltProduction)
    START_IMPROVEMENTS_OUT = (3, StartImprovements)
    LOOKING_FOR_EMPLOYEE_OUT = (4, LookingForEmployee)
    FIRE_EMPLOYEE_OUT = (5, FireEmployee)
    PAYMENT_OUT = (6, Payment)

    REVIEW_PERIOD = 5
    RESPONSE_DELAY = 1.5
    IDLE_THRESHOLD_REVIEWS = 3
    IMPROVEMENT_CAPITAL_THRESHOLD = 50.0
    IMPROVEMENTS_COOLDOWN_REVIEWS = 5

    def __init__(
        self,
        mfg_id: str,
        rd_id: str,
        producible_products: List[str],
        product_costs: Dict[str, float],
        markup_factor: float = 1.5,
        max_employees: int = 10,
    ):
        super().__init__(generateId("administration"))
        self._mfg_id = mfg_id
        self._rd_id = rd_id
        self._producible_products = producible_products
        self._product_costs = product_costs
        self._markup_factor = markup_factor
        self._max_employees = max_employees

        # State
        self.capital: float = 0.0
        self.available_employees: List[Employee] = []
        self.mfg_employees: List[Employee] = []
        self.rd_employees: List[Employee] = []
        self.pending_requests: List[RequestEmployee] = []
        self.halted_production: bool = False

        # Idle tracking for halt logic
        self._mfg_idle_reviews: int = 0
        self._got_mfg_request: bool = False

        # R&D improvement cooldown
        self._improvements_cooldown: int = 0
        self._improvement_product_index: int = 0

        # Output buffers
        self._out_assign_mfg: List[AssignEmployee] = []
        self._out_assign_rd: List[AssignEmployee] = []
        self._out_halt: List[HaltProduction] = []
        self._out_start_imp: List[StartImprovements] = []
        self._out_looking: List[LookingForEmployee] = []
        self._out_fire: List[FireEmployee] = []
        self._out_payment: List[Payment] = []

        # Register ports
        for port in [
            self.CAPITAL_IN, self.PAYMENT_IN, self.EMPLOYEE_OFFERING_IN,
            self.EMPLOYEE_RESIGNATION_IN, self.REQUEST_EMPLOYEE_IN,
            self.IMPROVEMENTS_COST_IN,
        ]:
            self.set_inport(port)
        for port in [
            self.ASSIGN_EMPLOYEE_MFG_OUT, self.ASSIGN_EMPLOYEE_RD_OUT,
            self.HALT_PRODUCTION_OUT, self.START_IMPROVEMENTS_OUT,
            self.LOOKING_FOR_EMPLOYEE_OUT, self.FIRE_EMPLOYEE_OUT,
            self.PAYMENT_OUT,
        ]:
            self.set_outport(port)

    # ------------------------------------------------------------------
    def _has_pending_output(self) -> bool:
        return bool(
            self._out_assign_mfg or self._out_assign_rd or self._out_halt
            or self._out_start_imp or self._out_looking or self._out_fire
            or self._out_payment
        )

    def _clear_buffers(self):
        self._out_assign_mfg.clear()
        self._out_assign_rd.clear()
        self._out_halt.clear()
        self._out_start_imp.clear()
        self._out_looking.clear()
        self._out_fire.clear()
        self._out_payment.clear()

    def _fulfill_requests(self):
        """Assign available employees to pending requests."""
        while self.pending_requests and self.available_employees:
            req = self.pending_requests.pop(0)
            emp = self.available_employees.pop(0)
            assign = AssignEmployee(generateId("assign_employee"), emp)

            if req.sender == self._mfg_id:
                self._out_assign_mfg.append(assign)
                self.mfg_employees.append(emp)
                if self.halted_production:
                    self.halted_production = False
                print(f"[ADMIN] {self.id} Assign {emp.id} -> Manufacturing")
            elif req.sender == self._rd_id:
                self._out_assign_rd.append(assign)
                self.rd_employees.append(emp)
                print(f"[ADMIN] {self.id} Assign {emp.id} -> R&D")

        # If still unfulfilled requests, look for employees externally
        if self.pending_requests and not self._out_looking:
            self._out_looking.append(LookingForEmployee(generateId("looking")))
            print(f"[ADMIN] {self.id} Looking for employee externally")

    def _remove_employee(self, emp: Employee):
        """Remove a resigning employee from whichever roster they're on."""
        for roster in [self.mfg_employees, self.rd_employees, self.available_employees]:
            for i, e in enumerate(roster):
                if e.id == emp.id:
                    roster.pop(i)
                    print(f"[ADMIN] {self.id} Employee {emp.id} resigned")
                    return

    # ------------------------------------------------------------------
    @override
    def delta_internal(self):
        self._clear_buffers()

        # --- Halt production check ---
        if self._got_mfg_request:
            self._mfg_idle_reviews = 0
            self._got_mfg_request = False
        else:
            self._mfg_idle_reviews += 1

        if (
            self.mfg_employees
            and self._mfg_idle_reviews >= self.IDLE_THRESHOLD_REVIEWS
            and not self.halted_production
        ):
            self._out_halt.append(HaltProduction(generateId("halt")))
            for emp in self.mfg_employees:
                self._out_fire.append(FireEmployee(generateId("fire"), emp))
            print(f"[ADMIN] {self.id} Halting production, firing {len(self.mfg_employees)} employees")
            self.mfg_employees.clear()
            self.halted_production = True

        # --- R&D improvements check ---
        if self._improvements_cooldown > 0:
            self._improvements_cooldown -= 1

        if (
            self.capital > self.IMPROVEMENT_CAPITAL_THRESHOLD
            and self._improvements_cooldown == 0
            and self._producible_products
        ):
            product = self._producible_products[
                self._improvement_product_index % len(self._producible_products)
            ]
            self._improvement_product_index += 1
            self._out_start_imp.append(
                StartImprovements(generateId("start_imp"), product)
            )
            self._improvements_cooldown = self.IMPROVEMENTS_COOLDOWN_REVIEWS
            print(f"[ADMIN] {self.id} Starting R&D improvements for '{product}'")

        # --- Fire excess employees ---
        total = len(self.mfg_employees) + len(self.rd_employees) + len(self.available_employees)
        while total > self._max_employees and self.available_employees:
            emp = self.available_employees.pop()
            self._out_fire.append(FireEmployee(generateId("fire"), emp))
            total -= 1
            print(f"[ADMIN] {self.id} Firing excess employee {emp.id}")

        # --- Try to fulfill any remaining pending requests ---
        self._fulfill_requests()

        print(f"[INTERNAL] {self.id} capital={self.capital:.1f} "
              f"employees(avail={len(self.available_employees)} "
              f"mfg={len(self.mfg_employees)} rd={len(self.rd_employees)})")

    @override
    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float):
        for port, bag in inputs.items():
            if port == self.CAPITAL_IN:
                for capital in cast(List[Capital], bag):
                    self.capital += capital.amount
                    print(f"[INPUT] {self.id} Received {capital}")

            elif port == self.PAYMENT_IN:
                for payment in cast(List[Payment], bag):
                    self.capital += payment.amount
                    print(f"[INPUT] {self.id} Received {payment}")

            elif port == self.EMPLOYEE_OFFERING_IN:
                for offering in cast(List[EmployeeOffering], bag):
                    self.available_employees.append(offering.employee)
                    print(f"[INPUT] {self.id} Received {offering}")

            elif port == self.EMPLOYEE_RESIGNATION_IN:
                for resignation in cast(List[EmployeeResignation], bag):
                    self._remove_employee(resignation.employee)
                    print(f"[INPUT] {self.id} Received {resignation}")

            elif port == self.REQUEST_EMPLOYEE_IN:
                for request in cast(List[RequestEmployee], bag):
                    self.pending_requests.append(request)
                    if request.sender == self._mfg_id:
                        self._got_mfg_request = True
                        if self.halted_production:
                            self.halted_production = False
                    print(f"[INPUT] {self.id} Received {request}")

            elif port == self.IMPROVEMENTS_COST_IN:
                for cost in cast(List[ImprovementsCost], bag):
                    self.capital -= cost.cost
                    print(f"[INPUT] {self.id} Received {cost} (capital now {self.capital:.1f})")

        self._fulfill_requests()

    @override
    def output(self) -> Dict[Port, List[Any]]:
        result: Dict[Port, List[Any]] = {}
        if self._out_assign_mfg:
            result[self.ASSIGN_EMPLOYEE_MFG_OUT] = deepcopy(self._out_assign_mfg)
        if self._out_assign_rd:
            result[self.ASSIGN_EMPLOYEE_RD_OUT] = deepcopy(self._out_assign_rd)
        if self._out_halt:
            result[self.HALT_PRODUCTION_OUT] = deepcopy(self._out_halt)
        if self._out_start_imp:
            result[self.START_IMPROVEMENTS_OUT] = deepcopy(self._out_start_imp)
        if self._out_looking:
            result[self.LOOKING_FOR_EMPLOYEE_OUT] = deepcopy(self._out_looking)
        if self._out_fire:
            result[self.FIRE_EMPLOYEE_OUT] = deepcopy(self._out_fire)
        if self._out_payment:
            result[self.PAYMENT_OUT] = deepcopy(self._out_payment)

        if result:
            print(f"[OUTPUT] {self.id} Sent {result}")
        return result

    def _needs_review(self) -> bool:
        """Return True if a periodic review is warranted."""
        if self.pending_requests:
            return True
        # Monitor for halt condition: mfg has employees but may be idle
        if self.mfg_employees:
            return True
        # Consider starting R&D improvements
        if (
            self.capital > self.IMPROVEMENT_CAPITAL_THRESHOLD
            and self._improvements_cooldown == 0
            and self._producible_products
        ):
            return True
        # Cooldown still ticking
        if self._improvements_cooldown > 0:
            return True
        return False

    @override
    def time_advance(self) -> Time:
        if self._has_pending_output():
            return self.RESPONSE_DELAY
        if self._needs_review():
            return self.REVIEW_PERIOD
        return float('inf')
