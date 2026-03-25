from copy import deepcopy
from typing import List, Any, Dict, Optional, cast, override

from src.devs.Atomic import Atomic
from src.devs.IdGenerator import generateId
from src.devs.Types import Port, Time
from src.examples.company.Messages import (
    AssignEmployee, UnassignEmployee, StartImprovements, Improvement,
    RequestEmployee, ImprovementsCost, InformImprovementFinished, Employee,
)


class RAndD(Atomic):
    """
    R&D atomic model.  Receives StartImprovements from Administration,
    requests an employee, works for improvement_duration, then sends
    an Improvement to Manufacturing, ImprovementsCost to Administration,
    and InformImprovementFinished to Administration.
    """

    # Phases
    IDLE = "idle"
    EMIT_COST = "emit_cost"        # emitting ImprovementsCost + RequestEmployee
    WAITING = "waiting"            # waiting for employee assignment
    WORKING = "working"            # producing improvement
    EMIT_RESULT = "emit_result"    # emitting Improvement + InformImprovementFinished

    # --- Input ports ---
    ASSIGN_EMPLOYEE_IN = (0, AssignEmployee)
    START_IMPROVEMENTS_IN = (1, StartImprovements)
    UNASSIGN_EMPLOYEE_IN = (2, UnassignEmployee)

    # --- Output ports ---
    IMPROVEMENT_OUT = (0, Improvement)
    REQUEST_EMPLOYEE_OUT = (1, RequestEmployee)
    IMPROVEMENTS_COST_OUT = (2, ImprovementsCost)
    INFORM_IMPROVEMENT_FINISHED_OUT = (3, InformImprovementFinished)

    PROCESSING_DELAY = 2.0

    def __init__(
        self,
        improvement_duration: float = 10.0,
        efficiency_gain: float = 0.1,
        improvement_cost: float = 20.0,
    ):
        super().__init__(generateId("r_and_d"))
        self.improvement_duration = improvement_duration
        self.efficiency_gain = efficiency_gain
        self.improvement_cost = improvement_cost

        self.phase: str = self.IDLE
        self.current_improvement: Optional[str] = None
        self.assigned_employees: List[Employee] = []

        # Output buffers
        self._out_improvement: List[Improvement] = []
        self._out_request_emp: List[RequestEmployee] = []
        self._out_cost: List[ImprovementsCost] = []
        self._out_inform_finished: List[InformImprovementFinished] = []

        # Queued improvement requests (if one arrives while busy)
        self._queued_improvements: List[str] = []

        # Register ports
        self.set_inports([
            self.ASSIGN_EMPLOYEE_IN, self.START_IMPROVEMENTS_IN,
            self.UNASSIGN_EMPLOYEE_IN,
        ])
        self.set_outports([
            self.IMPROVEMENT_OUT, self.REQUEST_EMPLOYEE_OUT,
            self.IMPROVEMENTS_COST_OUT, self.INFORM_IMPROVEMENT_FINISHED_OUT,
        ])

    # ------------------------------------------------------------------
    def _clear_buffers(self):
        self._out_improvement.clear()
        self._out_request_emp.clear()
        self._out_cost.clear()
        self._out_inform_finished.clear()

    def _start_next_queued(self):
        """If there's a queued improvement, begin it."""
        if self._queued_improvements and self.phase == self.IDLE:
            product_type = self._queued_improvements.pop(0)
            self.current_improvement = product_type
            self._out_cost.append(
                ImprovementsCost(generateId("imp_cost"), self.improvement_cost)
            )
            if not self.assigned_employees:
                self._out_request_emp.append(
                    RequestEmployee(generateId("req_emp"), self.id)
                )
            self.phase = self.EMIT_COST
            print(f"[R&D] {self.id} Starting improvement for '{product_type}'")

    # ------------------------------------------------------------------
    @override
    def delta_internal(self):
        self._clear_buffers()

        if self.phase == self.EMIT_COST:
            # Cost and request were emitted; transition to working or waiting
            if self.assigned_employees:
                self.phase = self.WORKING
                print(f"[R&D] {self.id} Working on '{self.current_improvement}'")
            else:
                self.phase = self.WAITING
                print(f"[R&D] {self.id} Waiting for employee")

        elif self.phase == self.WORKING:
            # Work complete — prepare improvement and finished notification
            if self.current_improvement is None:
                print(f"Error: {self.current_improvement} is None")
                exit(1)

            self._out_improvement.append(
                Improvement(
                    generateId("improvement"),
                    self.current_improvement,
                    self.efficiency_gain,
                )
            )
            self._out_inform_finished.append(
                InformImprovementFinished(
                    generateId("inform_finished"),
                    self.current_improvement,
                )
            )
            self.phase = self.EMIT_RESULT
            print(f"[R&D] {self.id} Completed improvement for '{self.current_improvement}'")

        elif self.phase == self.EMIT_RESULT:
            # Improvement was emitted; clean up
            self.current_improvement = None
            self.phase = self.IDLE
            # Start next queued improvement if any
            self._start_next_queued()

    @override
    def delta_external(self, inputs: Dict[Port, List[Any]], elapsed_time: float):
        for port, bag in inputs.items():
            if port == self.START_IMPROVEMENTS_IN:
                for start in cast(List[StartImprovements], bag):
                    print(f"[INPUT] {self.id} Received {start}")
                    if self.phase == self.IDLE:
                        self.current_improvement = start.product_type
                        self._out_cost.append(
                            ImprovementsCost(generateId("imp_cost"), self.improvement_cost)
                        )
                        if not self.assigned_employees:
                            self._out_request_emp.append(
                                RequestEmployee(generateId("req_emp"), self.id)
                            )
                        self.phase = self.EMIT_COST
                        print(f"[R&D] {self.id} Starting improvement for '{start.product_type}'")
                    else:
                        self._queued_improvements.append(start.product_type)
                        print(f"[R&D] {self.id} Queued improvement for '{start.product_type}'")

            elif port == self.ASSIGN_EMPLOYEE_IN:
                for assign in cast(List[AssignEmployee], bag):
                    self.assigned_employees.append(assign.employee)
                    print(f"[INPUT] {self.id} Received {assign}")
                    if self.phase == self.WAITING:
                        self.phase = self.WORKING
                        print(f"[R&D] {self.id} Employee arrived, working on "
                              f"'{self.current_improvement}'")

            elif port == self.UNASSIGN_EMPLOYEE_IN:
                for unassign in cast(List[UnassignEmployee], bag):
                    self.assigned_employees = [
                        e for e in self.assigned_employees
                        if e.id != unassign.employee.id
                    ]
                    print(f"[INPUT] {self.id} Received {unassign}")

    @override
    def output(self) -> Dict[Port, List[Any]]:
        result: Dict[Port, List[Any]] = {}
        if self._out_improvement:
            result[self.IMPROVEMENT_OUT] = deepcopy(self._out_improvement)
        if self._out_request_emp:
            result[self.REQUEST_EMPLOYEE_OUT] = deepcopy(self._out_request_emp)
        if self._out_cost:
            result[self.IMPROVEMENTS_COST_OUT] = deepcopy(self._out_cost)
        if self._out_inform_finished:
            result[self.INFORM_IMPROVEMENT_FINISHED_OUT] = deepcopy(self._out_inform_finished)

        for _, messages in result.items():
            print(f"[OUTPUT] {self.id} Sent {messages}")
        return result

    @override
    def time_advance(self) -> Time:
        if self.phase == self.IDLE:
            return float('inf')
        elif self.phase == self.EMIT_COST:
            return self.PROCESSING_DELAY
        elif self.phase == self.WAITING:
            return float('inf')
        elif self.phase == self.WORKING:
            return self.improvement_duration
        elif self.phase == self.EMIT_RESULT:
            return self.PROCESSING_DELAY
        return float('inf')
