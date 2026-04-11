from copy import deepcopy
from typing import List, Any, Dict, cast, override

from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Port, Time
from src.examples.company.Messages import (
    Capital, Payment, EmployeeOffering, EmployeeResignation,
    RequestEmployee, ImprovementsCost, AssignEmployee, UnassignEmployee,
    ForceHaltProduction, UndoHaltProduction, StartImprovements,
    LookingForEmployee, FireEmployee, Employee, DemandProduct,
    OfferProduct, InformImprovementFinished,
)


class Administration(Atomic):
    # --- Input ports ---
    CAPITAL_IN = (0, Capital)
    PAYMENT_IN = (1, Payment)
    EMPLOYEE_OFFERING_IN = (2, EmployeeOffering)
    EMPLOYEE_RESIGNATION_IN = (3, EmployeeResignation)
    REQUEST_EMPLOYEE_IN = (4, RequestEmployee)
    IMPROVEMENTS_COST_IN = (5, ImprovementsCost)
    DEMAND_PRODUCT_IN = (6, DemandProduct)
    OFFER_PRODUCT_IN = (7, OfferProduct)
    INFORM_IMPROVEMENT_FINISHED_IN = (8, InformImprovementFinished)

    # --- Output ports ---
    ASSIGN_EMPLOYEE_MFG_OUT = (0, AssignEmployee)
    ASSIGN_EMPLOYEE_RD_OUT = (1, AssignEmployee)
    UNASSIGN_EMPLOYEE_MFG_OUT = (2, UnassignEmployee)
    UNASSIGN_EMPLOYEE_RD_OUT = (3, UnassignEmployee)
    FORCE_HALT_PRODUCTION_OUT = (4, ForceHaltProduction)
    UNDO_HALT_PRODUCTION_OUT = (5, UndoHaltProduction)
    START_IMPROVEMENTS_OUT = (6, StartImprovements)
    LOOKING_FOR_EMPLOYEE_OUT = (7, LookingForEmployee)
    FIRE_EMPLOYEE_OUT = (8, FireEmployee)
    DEMAND_PRODUCT_OUT = (9, DemandProduct)
    PAYMENT_OUT = (10, Payment)

    REVIEW_PERIOD = 5
    RESPONSE_DELAY = 1.5
    IDLE_THRESHOLD_REVIEWS = 3
    IMPROVEMENT_CAPITAL_THRESHOLD = 50.0

    def __init__(
        self,
        mfg_id: str,
        rnd_id: str,
        producible_products: List[str],
        max_employees: int = 10,
    ):
        super().__init__(generateId("administration"))
        self._mfg_id = mfg_id
        self._rnd_id = rnd_id
        self._producible_products = producible_products
        self._max_employees = max_employees

        # State
        self.capital: float = 0.0
        self.available_employees: List[Employee] = []
        self.mfg_employees: List[Employee] = []
        self.rd_employees: List[Employee] = []
        self.pending_requests: List[RequestEmployee] = []
        self.halted_production: bool = False

        # Demand tracking for halt logic (spec line 76-77):
        # tracks whether any activity from Manufacturing was seen this period.
        self._mfg_activity_this_period: bool = False
        self._no_activity_reviews: int = 0

        # R&D improvement tracking: track whether R&D is currently busy
        self._rd_busy: bool = False
        self._improvement_product_index: int = 0

        # Output buffers
        self._out_assign_mfg: List[AssignEmployee] = []
        self._out_assign_rd: List[AssignEmployee] = []
        self._out_unassign_mfg: List[UnassignEmployee] = []
        self._out_unassign_rd: List[UnassignEmployee] = []
        self._out_force_halt: List[ForceHaltProduction] = []
        self._out_undo_halt: List[UndoHaltProduction] = []
        self._out_start_imp: List[StartImprovements] = []
        self._out_looking: List[LookingForEmployee] = []
        self._out_fire: List[FireEmployee] = []
        self._out_demand: List[DemandProduct] = []
        self._out_payment: List[Payment] = []

        # Register ports
        self.set_inports([
            self.CAPITAL_IN, self.PAYMENT_IN, self.EMPLOYEE_OFFERING_IN,
            self.EMPLOYEE_RESIGNATION_IN, self.REQUEST_EMPLOYEE_IN,
            self.IMPROVEMENTS_COST_IN, self.DEMAND_PRODUCT_IN,
            self.OFFER_PRODUCT_IN, self.INFORM_IMPROVEMENT_FINISHED_IN,
        ])
        self.set_outports([
            self.ASSIGN_EMPLOYEE_MFG_OUT, self.ASSIGN_EMPLOYEE_RD_OUT,
            self.UNASSIGN_EMPLOYEE_MFG_OUT, self.UNASSIGN_EMPLOYEE_RD_OUT,
            self.FORCE_HALT_PRODUCTION_OUT, self.UNDO_HALT_PRODUCTION_OUT,
            self.START_IMPROVEMENTS_OUT, self.LOOKING_FOR_EMPLOYEE_OUT,
            self.FIRE_EMPLOYEE_OUT, self.DEMAND_PRODUCT_OUT,
            self.PAYMENT_OUT,
        ])

    # ------------------------------------------------------------------
    def _has_pending_output(self) -> bool:
        return bool(
            self._out_assign_mfg or self._out_assign_rd
            or self._out_unassign_mfg or self._out_unassign_rd
            or self._out_force_halt or self._out_undo_halt
            or self._out_start_imp or self._out_looking or self._out_fire
            or self._out_demand or self._out_payment
        )

    def _clear_buffers(self):
        self._out_assign_mfg.clear()
        self._out_assign_rd.clear()
        self._out_unassign_mfg.clear()
        self._out_unassign_rd.clear()
        self._out_force_halt.clear()
        self._out_undo_halt.clear()
        self._out_start_imp.clear()
        self._out_looking.clear()
        self._out_fire.clear()
        self._out_demand.clear()
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
                print(f"[ADMIN] {self.id} Assign {emp.id} -> Manufacturing")
            elif req.sender == self._rnd_id:
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

        # --- Halt production check (spec line 76-77) ---
        # Halt when no Manufacturing activity for several reviews
        if self._mfg_activity_this_period:
            self._no_activity_reviews = 0
        else:
            self._no_activity_reviews += 1
        self._mfg_activity_this_period = False

        if (
            not self.halted_production
            and self._no_activity_reviews >= self.IDLE_THRESHOLD_REVIEWS
            and self.mfg_employees
        ):
            self._out_force_halt.append(
                ForceHaltProduction(generateId("force_halt"))
            )
            # Unassign manufacturing employees back to available pool
            for emp in self.mfg_employees:
                self._out_unassign_mfg.append(
                    UnassignEmployee(generateId("unassign"), emp)
                )
                self.available_employees.append(emp)
            self.mfg_employees.clear()
            self.halted_production = True
            print(f"[ADMIN] {self.id} Halting production — no demand, "
                  f"employees idle")

        # --- Undo halt if activity has returned ---
        if (
            self.halted_production
            and self._no_activity_reviews == 0
        ):
            self._out_undo_halt.append(
                UndoHaltProduction(generateId("undo_halt"))
            )
            self.halted_production = False
            print(f"[ADMIN] {self.id} Resuming production — demand returned")

        # --- R&D improvements check ---
        if (
            not self._rd_busy
            and self.capital > self.IMPROVEMENT_CAPITAL_THRESHOLD
            and self._producible_products
        ):
            product = self._producible_products[
                self._improvement_product_index % len(self._producible_products)
            ]
            self._improvement_product_index += 1
            self._out_start_imp.append(
                StartImprovements(generateId("start_improvement"), product)
            )
            self._rd_busy = True
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
                        self._mfg_activity_this_period = True
                    print(f"[INPUT] {self.id} Received {request}")

            elif port == self.IMPROVEMENTS_COST_IN:
                for cost in cast(List[ImprovementsCost], bag):
                    self.capital -= cost.cost
                    print(f"[INPUT] {self.id} Received {cost} "
                          f"(capital now {self.capital:.1f})")

            elif port == self.DEMAND_PRODUCT_IN:
                for dp in cast(List[DemandProduct], bag):
                    self._mfg_activity_this_period = True
                    # Forward to external (pass-through)
                    self._out_demand.append(dp)
                    print(f"[INPUT] {self.id} Received {dp} (demand tracked)")

            elif port == self.OFFER_PRODUCT_IN:
                for offer in cast(List[OfferProduct], bag):
                    # Pay for the offered product
                    self.capital -= offer.cost
                    self._out_payment.append(
                        Payment(generateId("payment"), offer.cost)
                    )
                    print(f"[INPUT] {self.id} Received {offer}, paid {offer.cost:.1f} "
                          f"(capital now {self.capital:.1f})")

            elif port == self.INFORM_IMPROVEMENT_FINISHED_IN:
                for info in cast(List[InformImprovementFinished], bag):
                    self._rd_busy = False
                    print(f"[INPUT] {self.id} Received {info} — R&D available")

        self._fulfill_requests()

    @override
    def output(self) -> Dict[Port, List[Any]]:
        result: Dict[Port, List[Any]] = {}
        if self._out_assign_mfg:
            result[self.ASSIGN_EMPLOYEE_MFG_OUT] = deepcopy(self._out_assign_mfg)
        if self._out_assign_rd:
            result[self.ASSIGN_EMPLOYEE_RD_OUT] = deepcopy(self._out_assign_rd)
        if self._out_unassign_mfg:
            result[self.UNASSIGN_EMPLOYEE_MFG_OUT] = deepcopy(self._out_unassign_mfg)
        if self._out_unassign_rd:
            result[self.UNASSIGN_EMPLOYEE_RD_OUT] = deepcopy(self._out_unassign_rd)
        if self._out_force_halt:
            result[self.FORCE_HALT_PRODUCTION_OUT] = deepcopy(self._out_force_halt)
        if self._out_undo_halt:
            result[self.UNDO_HALT_PRODUCTION_OUT] = deepcopy(self._out_undo_halt)
        if self._out_start_imp:
            result[self.START_IMPROVEMENTS_OUT] = deepcopy(self._out_start_imp)
        if self._out_looking:
            result[self.LOOKING_FOR_EMPLOYEE_OUT] = deepcopy(self._out_looking)
        if self._out_fire:
            result[self.FIRE_EMPLOYEE_OUT] = deepcopy(self._out_fire)
        if self._out_demand:
            result[self.DEMAND_PRODUCT_OUT] = deepcopy(self._out_demand)
        if self._out_payment:
            result[self.PAYMENT_OUT] = deepcopy(self._out_payment)

        for _, messages in result.items():
            print(f"[OUTPUT] {self.id} Sent {messages}")

        return result

    def _needs_review(self) -> bool:
        """Return True if a periodic review is warranted.

        When halted, Administration goes passive and relies on
        delta_external to wake it (new demand arrives via
        DemandProduct -> Manufacturing -> RequestEmployee -> Admin).
        """
        if self.pending_requests:
            return True
        # Monitor for halt condition: mfg has employees but may be idle
        if self.mfg_employees:
            return True
        # Consider starting R&D improvements
        if (
            not self._rd_busy
            and self.capital > self.IMPROVEMENT_CAPITAL_THRESHOLD
            and self._producible_products
        ):
            return True
        return False

    @override
    def time_advance(self) -> Time:
        if self._has_pending_output():
            return self.RESPONSE_DELAY
        if self._needs_review():
            return self.REVIEW_PERIOD
        return float('inf')
