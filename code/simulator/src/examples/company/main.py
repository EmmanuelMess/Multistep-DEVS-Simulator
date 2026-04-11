import math
import random
import sys
from collections import defaultdict
from typing import List, Tuple, Any, Dict

from src.devs.AtomicGraph import AtomicGraph
from src.devs.IdGenerator import generateId
from src.devs.Simulator import Simulator
from src.devs.Types import Port, Time
from src.examples.company.Administration import Administration
from src.examples.company.ExternalSource import ExternalSource
from src.examples.company.Manufacturing import Manufacturing
from src.examples.company.RAndD import RAndD
from src.examples.company.Messages import (
    Capital, Payment, DemandProduct, Product, Employee,
    EmployeeOffering, EmployeeResignation, OfferProduct,
)

# ---------------------------------------------------------------------------
# Simulation configuration
# ---------------------------------------------------------------------------

PRODUCT_CONFIG: Dict[str, Dict[str, Any]] = {
    "steel":  {"role": "primary", "cost": 3.0},
    "widget": {"role": "final", "cost": 12.0},
}

BILL_OF_MATERIALS: Dict[str, Dict[str, Any]] = {
    "widget": {
        "inputs": {"steel": 2},
        "base_time": 5.0,
    },
}

PRODUCIBLE_PRODUCTS = [
    pt for pt, cfg in PRODUCT_CONFIG.items() if cfg["role"] in ("final", "intermediate")
]

PRODUCT_COSTS: Dict[str, float] = {
    pt: cfg.get("cost", 0.0) for pt, cfg in PRODUCT_CONFIG.items()
}


# ---------------------------------------------------------------------------
# Event generators
# ---------------------------------------------------------------------------

def generate_scripted_events() -> Dict[Time, List[Tuple[Port, Any]]]:
    """Hand-crafted event list for a deterministic scenario.

    Exercises every message type and major state transition:
    - Capital injection
    - Employee offerings (multiple)
    - DemandProduct for widgets -> Manufacturing requests raw materials
    - Product (steel) deliveries
    - Production cycle, shipment from inventory
    - OfferProduct from outside -> Administration pays
    - Payment from customers (honor system)
    - R&D improvement start, completion, efficiency gain
    - Employee resignation mid-cycle
    - Halt production when demand dries up
    - Demand returns -> undo halt
    - FireEmployee / LookingForEmployee (triggered internally)
    """
    events: Dict[Time, List[Tuple[Port, Any]]] = defaultdict(list)
    employees: List[Employee] = []

    # t=1: Initial capital injection
    events[1.0].append((ExternalSource.CAPITAL_OUT,
                    Capital(generateId("capital"), 200.0)))

    # t=2,4: Employees arrive early
    for t in [2.0, 4.0]:
        employee = Employee(generateId("employee"))
        events[t].append((ExternalSource.EMPLOYEE_OFFERING_OUT,
                      EmployeeOffering(generateId("employee_offer"), employee)))
        employees.append(employee)

    # t=3: First demand for a widget
    events[3.0].append((ExternalSource.DEMAND_PRODUCT_OUT,
                    DemandProduct(generateId("demand"), "widget")))

    # t=5,6: Steel deliveries (2 needed per widget)
    events[5.0].append((ExternalSource.PRODUCT_OUT,
                    Product(generateId("product"), "steel")))
    events[6.0].append((ExternalSource.PRODUCT_OUT,
                    Product(generateId("product"), "steel")))

    # t=7: Payment from customer for the first widget (honor system)
    events[7.0].append((ExternalSource.PAYMENT_OUT,
                    Payment(generateId("payment"), 12.0)))

    # t=8: Third employee arrives
    emp3 = Employee(generateId("employee"))
    events[8.0].append((ExternalSource.EMPLOYEE_OFFERING_OUT,
                    EmployeeOffering(generateId("employee_offer"), emp3)))
    employees.append(emp3)

    # t=9,10: More demand + steel for a second widget
    events[9.0].append((ExternalSource.DEMAND_PRODUCT_OUT,
                    DemandProduct(generateId("demand"), "widget")))
    events[10.0].append((ExternalSource.PRODUCT_OUT,
                     Product(generateId("product"), "steel")))
    events[10.5].append((ExternalSource.PRODUCT_OUT,
                     Product(generateId("product"), "steel")))

    # t=11: Payment for second widget
    events[11.0].append((ExternalSource.PAYMENT_OUT,
                     Payment(generateId("payment"), 12.0)))

    # t=12: Outside offers steel to the company (Administration pays)
    events[12.0].append((ExternalSource.OFFER_PRODUCT_OUT,
                     OfferProduct(generateId("offer"), "steel", 3.0)))

    # t=14: Third demand + more steel
    events[14.0].append((ExternalSource.DEMAND_PRODUCT_OUT,
                     DemandProduct(generateId("demand"), "widget")))
    events[14.5].append((ExternalSource.PRODUCT_OUT,
                     Product(generateId("product"), "steel")))
    events[15.0].append((ExternalSource.PRODUCT_OUT,
                     Product(generateId("product"), "steel")))
    events[16.0].append((ExternalSource.PAYMENT_OUT,
                     Payment(generateId("payment"), 12.0)))

    # t=20: Fourth employee arrives
    emp4 = Employee(generateId("employee"))
    events[20.0].append((ExternalSource.EMPLOYEE_OFFERING_OUT,
                     EmployeeOffering(generateId("employee_offer"), emp4)))
    employees.append(emp4)

    # t=25: Employee resignation (second employee resigns)
    events[25.0].append((ExternalSource.EMPLOYEE_RESIGNATION_OUT,
                     EmployeeResignation(generateId("resign"), employees[1])))

    # --- GAP: no demand from t=16 to t=55 ---
    # Administration should halt production after IDLE_THRESHOLD_REVIEWS

    # t=55: Demand returns -> triggers undo halt
    events[55.0].append((ExternalSource.DEMAND_PRODUCT_OUT,
                     DemandProduct(generateId("demand"), "widget")))
    events[56.0].append((ExternalSource.PRODUCT_OUT,
                     Product(generateId("product"), "steel")))
    events[56.5].append((ExternalSource.PRODUCT_OUT,
                     Product(generateId("product"), "steel")))
    events[58.0].append((ExternalSource.PAYMENT_OUT,
                     Payment(generateId("payment"), 12.0)))

    # t=60: Fifth employee (to trigger FireEmployee if over max)
    employee = Employee(generateId("employee"))
    events[60.0].append((ExternalSource.EMPLOYEE_OFFERING_OUT,
                     EmployeeOffering(generateId("employee_offer"), employee)))
    employees.append(employee)

    return dict(events)


def generate_random_events(
    seed: int = 42,
    max_time: float = 100.0,
) -> Dict[Time, List[Tuple[Port, Any]]]:
    """Generate events from exponential inter-arrival distributions.

    Exercises all message types via random scheduling.
    """
    rng = random.Random(seed)
    e: Dict[Time, List[Tuple[Port, Any]]] = defaultdict(list)

    # Capital — one-shot at start
    e[0.5].append((ExternalSource.CAPITAL_OUT,
                    Capital(generateId("capital"), 200.0)))

    # Customer demand (exponential, mean 5.0)
    t = 0.0
    for _ in range(40):
        t += rng.expovariate(1.0 / 5.0)
        if t > max_time:
            break
        e[round(t, 4)].append((ExternalSource.DEMAND_PRODUCT_OUT,
                                DemandProduct(generateId("demand"), "widget")))

    # Raw material deliveries (exponential, mean 3.0)
    t = 1.0
    for _ in range(60):
        t += rng.expovariate(1.0 / 3.0)
        if t > max_time:
            break
        e[round(t, 4)].append((ExternalSource.PRODUCT_OUT,
                                Product(generateId("product"), "steel")))

    # Employee offerings (exponential, mean 8.0)
    employees: List[Employee] = []
    t = 1.0
    for _ in range(15):
        t += rng.expovariate(1.0 / 8.0)
        if t > max_time:
            break
        employee = Employee(generateId("employee"))
        employees.append(employee)
        e[round(t, 4)].append((ExternalSource.EMPLOYEE_OFFERING_OUT,
                                EmployeeOffering(generateId("employee_offer"), employee)))

    # Payments (follow demand with some delay)
    t = 3.0
    for _ in range(30):
        t += rng.expovariate(1.0 / 6.0)
        if t > max_time:
            break
        pay = round(rng.uniform(8.0, 15.0), 2)
        e[round(t, 4)].append((ExternalSource.PAYMENT_OUT,
                                Payment(generateId("payment"), pay)))

    # Outside offers products to the company (exponential, mean 15.0)
    t = 5.0
    for _ in range(10):
        t += rng.expovariate(1.0 / 15.0)
        if t > max_time:
            break
        cost = round(rng.uniform(2.0, 5.0), 2)
        e[round(t, 4)].append((ExternalSource.OFFER_PRODUCT_OUT,
                                OfferProduct(generateId("offer"), "steel", cost)))

    # Employee resignations (sparse, exponential, mean 30.0)
    t = 20.0
    for _ in range(3):
        t += rng.expovariate(1.0 / 30.0)
        if t > max_time or not employees:
            break
        employee = rng.choice(employees)
        employees.remove(employee)
        e[round(t, 4)].append((ExternalSource.EMPLOYEE_RESIGNATION_OUT,
                                EmployeeResignation(generateId("resign"), employee)))

    return dict(e)


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------

def build_graph(events: Dict[Time, List[Tuple[Port, Any]]]) -> Tuple[AtomicGraph, Simulator]:
    graph = AtomicGraph()
    simulator = Simulator(graph)

    # --- Create models ---
    manufacturing = Manufacturing(
        bill_of_materials=BILL_OF_MATERIALS,
        product_costs=PRODUCT_COSTS,
    )
    rnd = RAndD(
        improvement_duration=10.0,
        efficiency_gain=0.1,
        improvement_cost=20.0,
    )
    admin = Administration(
        mfg_id=manufacturing.id,
        rnd_id=rnd.id,
        producible_products=PRODUCIBLE_PRODUCTS,
        max_employees=10,
    )
    source = ExternalSource(events)

    graph.add_all([manufacturing, rnd, admin, source])

    # --- Internal connections (per DEVS diagram) ---

    # Administration -> Manufacturing:
    #   { ForceHaltProduction, UndoHaltProduction,
    #     AssignEmployee, UnassignEmployee }
    graph.connect(admin.id, admin.ASSIGN_EMPLOYEE_MFG_OUT, manufacturing.id, manufacturing.ASSIGN_EMPLOYEE_IN)
    graph.connect(admin.id, admin.UNASSIGN_EMPLOYEE_MFG_OUT, manufacturing.id, manufacturing.UNASSIGN_EMPLOYEE_IN)
    graph.connect(admin.id, admin.FORCE_HALT_PRODUCTION_OUT, manufacturing.id, manufacturing.FORCE_HALT_PRODUCTION_IN)
    graph.connect(admin.id, admin.UNDO_HALT_PRODUCTION_OUT, manufacturing.id, manufacturing.UNDO_HALT_PRODUCTION_IN)

    # Manufacturing -> Administration:
    #   { RequestEmployee, DemandProduct(Product(i)) }
    graph.connect(manufacturing.id, manufacturing.REQUEST_EMPLOYEE_OUT, admin.id, admin.REQUEST_EMPLOYEE_IN)
    graph.connect(manufacturing.id, manufacturing.DEMAND_PRODUCT_OUT, admin.id, admin.DEMAND_PRODUCT_IN)

    # Administration -> R&D:
    #   { AssignEmployee, UnassignEmployee, StartImprovements }
    graph.connect(admin.id, admin.ASSIGN_EMPLOYEE_RD_OUT, rnd.id, rnd.ASSIGN_EMPLOYEE_IN)
    graph.connect(admin.id, admin.UNASSIGN_EMPLOYEE_RD_OUT, rnd.id, rnd.UNASSIGN_EMPLOYEE_IN)
    graph.connect(admin.id, admin.START_IMPROVEMENTS_OUT, rnd.id, rnd.START_IMPROVEMENTS_IN)

    # R&D -> Administration:
    #   { RequestEmployee, ImprovementsCost, InformImprovementFinished }
    graph.connect(rnd.id, rnd.REQUEST_EMPLOYEE_OUT, admin.id, admin.REQUEST_EMPLOYEE_IN)
    graph.connect(rnd.id, rnd.IMPROVEMENTS_COST_OUT, admin.id, admin.IMPROVEMENTS_COST_IN)
    graph.connect(rnd.id, rnd.INFORM_IMPROVEMENT_FINISHED_OUT, admin.id, admin.INFORM_IMPROVEMENT_FINISHED_IN)

    # R&D -> Manufacturing: { Improvement }
    graph.connect(rnd.id, rnd.IMPROVEMENT_OUT,
                  manufacturing.id, manufacturing.IMPROVEMENT_IN)

    # --- External connections (ExternalSource -> Company inputs) ---

    # Capital, Payment -> Administration
    graph.connect(source.id, source.CAPITAL_OUT, admin.id, admin.CAPITAL_IN)
    graph.connect(source.id, source.PAYMENT_OUT, admin.id, admin.PAYMENT_IN)

    # EmployeeOffering, EmployeeResignation, OfferProduct -> Administration
    graph.connect(source.id, source.EMPLOYEE_OFFERING_OUT, admin.id, admin.EMPLOYEE_OFFERING_IN)
    graph.connect(source.id, source.EMPLOYEE_RESIGNATION_OUT, admin.id, admin.EMPLOYEE_RESIGNATION_IN)
    graph.connect(source.id, source.OFFER_PRODUCT_OUT, admin.id, admin.OFFER_PRODUCT_IN)

    # DemandProduct -> Manufacturing
    graph.connect(source.id, source.DEMAND_PRODUCT_OUT, manufacturing.id, manufacturing.DEMAND_PRODUCT_IN)

    # Product (raw materials) -> Manufacturing
    graph.connect(source.id, source.PRODUCT_OUT, manufacturing.id, manufacturing.PRODUCT_IN)

    # Company outputs (Product, OfferProduct from Manufacturing;
    # LookingForEmployee, FireEmployee, DemandProduct, Payment
    # from Administration) are unconnected — they print to console
    # via the models' output() methods.

    return graph, simulator


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(mode: str = "scripted"):
    if mode == "scripted":
        events = generate_scripted_events()
    elif mode == "random":
        events = generate_random_events()
    else:
        raise ValueError(f"Unknown mode: {mode}")

    graph, simulator = build_graph(events)

    print(f"=== Company Simulation ({mode} mode) ===\n")

    next_time = graph.min_next_time(simulator.time)
    while math.isfinite(next_time):
        print(f"\n== Time {next_time} ==")
        simulator.simulate_step()
        next_time = graph.min_next_time(simulator.time)

    print("\n=== Simulation complete ===")


if __name__ == '__main__':
    main(sys.argv[1])
