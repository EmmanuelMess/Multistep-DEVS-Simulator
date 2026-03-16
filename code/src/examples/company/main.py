import math
import random
from typing import List, Tuple, Any

from src.devs.AtomicGraph import AtomicGraph
from src.devs.IdGenerator import generateId
from src.devs.Simulator import Simulator
from src.devs.Types import Port
from src.examples.company.Administration import Administration
from src.examples.company.ExternalSource import ExternalSource
from src.examples.company.Manufacturing import Manufacturing
from src.examples.company.RAndD import RAndD
from src.examples.company.Messages import (
    Capital, Payment, DemandProduct, Product, Employee,
    EmployeeOffering, EmployeeResignation,
)

# ---------------------------------------------------------------------------
# Simulation configuration
# ---------------------------------------------------------------------------

PRODUCT_CONFIG = {
    "steel":  {"role": "primary", "cost": 3.0},
    "widget": {"role": "final"},
}

BILL_OF_MATERIALS = {
    "widget": {
        "inputs": {"steel": 2},
        "base_time": 5.0,
    },
}

PRODUCIBLE_PRODUCTS = [
    pt for pt, cfg in PRODUCT_CONFIG.items() if cfg["role"] in ("final", "intermediate")
]

PRODUCT_COSTS = {
    pt: cfg["cost"] for pt, cfg in PRODUCT_CONFIG.items() if "cost" in cfg
}


# ---------------------------------------------------------------------------
# Event generators
# ---------------------------------------------------------------------------

def generate_scripted_events() -> List[Tuple[float, Port, Any]]:
    """Hand-crafted event list for a deterministic scenario."""
    events = []

    # Initial capital injection
    events.append((1.0, ExternalSource.CAPITAL_OUT, Capital(generateId("capital"), 100.0)))

    # Employees arrive over time
    for i, t in enumerate([2.0, 4.0, 8.0, 15.0]):
        emp = Employee(generateId("employee"))
        events.append((t, ExternalSource.EMPLOYEE_OFFERING_OUT,
                        EmployeeOffering(generateId("emp_offer"), emp)))

    # Customer demand for widgets
    for t in [3.0, 6.0, 10.0, 14.0, 18.0, 22.0, 30.0, 35.0]:
        events.append((t, ExternalSource.DEMAND_PRODUCT_OUT,
                        DemandProduct(generateId("demand"), "widget")))

    # Raw material deliveries (steel)
    for t in [5.0, 7.0, 9.0, 11.0, 13.0, 16.0, 20.0, 24.0, 28.0, 32.0, 36.0]:
        events.append((t, ExternalSource.PRODUCT_OUT,
                        Product(generateId("product"), "steel")))

    # Payments for products we ship (honor system — the outside pays after some delay)
    for t in [25.0, 33.0, 40.0]:
        events.append((t, ExternalSource.PAYMENT_OUT,
                        Payment(generateId("payment"), 10.0)))

    # An employee resigns midway
    # (We pick a symbolic id — matches by id field, not object identity)
    events.append((26.0, ExternalSource.EMPLOYEE_RESIGNATION_OUT,
                    EmployeeResignation(generateId("resign"),
                                        Employee("<employee:2>"))))

    return events


def generate_random_events(
    seed: int = 42,
    max_time: float = 100.0,
) -> List[Tuple[float, Port, Any]]:
    """Generate events from exponential inter-arrival distributions."""
    rng = random.Random(seed)
    events: List[Tuple[float, Port, Any]] = []

    # Capital — one-shot at start
    events.append((0.5, ExternalSource.CAPITAL_OUT,
                    Capital(generateId("capital"), 100.0)))

    # Customer demand (exponential, mean 5.0)
    t = 0.0
    for _ in range(40):
        t += rng.expovariate(1.0 / 5.0)
        if t > max_time:
            break
        events.append((t, ExternalSource.DEMAND_PRODUCT_OUT,
                        DemandProduct(generateId("demand"), "widget")))

    # Raw material deliveries (exponential, mean 3.0)
    t = 1.0
    for _ in range(60):
        t += rng.expovariate(1.0 / 3.0)
        if t > max_time:
            break
        events.append((t, ExternalSource.PRODUCT_OUT,
                        Product(generateId("product"), "steel")))

    # Employee offerings (exponential, mean 8.0)
    t = 1.0
    for _ in range(15):
        t += rng.expovariate(1.0 / 8.0)
        if t > max_time:
            break
        emp = Employee(generateId("employee"))
        events.append((t, ExternalSource.EMPLOYEE_OFFERING_OUT,
                        EmployeeOffering(generateId("emp_offer"), emp)))

    # Payments (exponential, mean 10.0, smaller count)
    t = 15.0
    for _ in range(20):
        t += rng.expovariate(1.0 / 10.0)
        if t > max_time:
            break
        events.append((t, ExternalSource.PAYMENT_OUT,
                        Payment(generateId("payment"),
                                round(rng.uniform(5.0, 20.0), 2))))

    return events


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------

def build_graph(events: List[Tuple[float, Port, Any]]) -> Tuple[AtomicGraph, Simulator]:
    graph = AtomicGraph()
    simulator = Simulator(graph)

    # --- Create models ---
    manufacturing = Manufacturing(
        bill_of_materials=BILL_OF_MATERIALS,
        product_config=PRODUCT_CONFIG,
    )
    rd = RAndD(
        improvement_duration=10.0,
        efficiency_gain=0.1,
        improvement_cost=20.0,
    )
    admin = Administration(
        mfg_id=manufacturing.id,
        rd_id=rd.id,
        producible_products=PRODUCIBLE_PRODUCTS,
        product_costs=PRODUCT_COSTS,
        markup_factor=1.5,
        max_employees=10,
    )
    source = ExternalSource(events)

    graph.add(manufacturing)
    graph.add(rd)
    graph.add(admin)
    graph.add(source)

    # --- Internal connections (per DEVS diagram) ---

    # Administration -> Manufacturing: { AssignEmployee, HaltProduction }
    graph.connect(admin.id, admin.ASSIGN_EMPLOYEE_MFG_OUT,
                  manufacturing.id, manufacturing.ASSIGN_EMPLOYEE_IN)
    graph.connect(admin.id, admin.HALT_PRODUCTION_OUT,
                  manufacturing.id, manufacturing.HALT_PRODUCTION_IN)

    # Manufacturing -> Administration: { RequestEmployee }
    graph.connect(manufacturing.id, manufacturing.REQUEST_EMPLOYEE_OUT,
                  admin.id, admin.REQUEST_EMPLOYEE_IN)

    # Administration -> R&D: { AssignEmployee, StartImprovements }
    graph.connect(admin.id, admin.ASSIGN_EMPLOYEE_RD_OUT,
                  rd.id, rd.ASSIGN_EMPLOYEE_IN)
    graph.connect(admin.id, admin.START_IMPROVEMENTS_OUT,
                  rd.id, rd.START_IMPROVEMENTS_IN)

    # R&D -> Administration: { RequestEmployee, ImprovementsCost }
    graph.connect(rd.id, rd.REQUEST_EMPLOYEE_OUT,
                  admin.id, admin.REQUEST_EMPLOYEE_IN)
    graph.connect(rd.id, rd.IMPROVEMENTS_COST_OUT,
                  admin.id, admin.IMPROVEMENTS_COST_IN)

    # R&D -> Manufacturing: { Improvement }
    graph.connect(rd.id, rd.IMPROVEMENT_OUT,
                  manufacturing.id, manufacturing.IMPROVEMENT_IN)

    # --- External connections (ExternalSource -> Company inputs) ---

    # Capital, Payment -> Administration
    graph.connect(source.id, source.CAPITAL_OUT,
                  admin.id, admin.CAPITAL_IN)
    graph.connect(source.id, source.PAYMENT_OUT,
                  admin.id, admin.PAYMENT_IN)

    # EmployeeOffering, EmployeeResignation -> Administration
    graph.connect(source.id, source.EMPLOYEE_OFFERING_OUT,
                  admin.id, admin.EMPLOYEE_OFFERING_IN)
    graph.connect(source.id, source.EMPLOYEE_RESIGNATION_OUT,
                  admin.id, admin.EMPLOYEE_RESIGNATION_IN)

    # DemandProduct -> Manufacturing
    graph.connect(source.id, source.DEMAND_PRODUCT_OUT,
                  manufacturing.id, manufacturing.DEMAND_PRODUCT_IN)

    # Product (raw materials) -> Manufacturing
    graph.connect(source.id, source.PRODUCT_OUT,
                  manufacturing.id, manufacturing.PRODUCT_IN)

    # Company outputs (Product, DemandProduct, OfferProduct from Manufacturing;
    # LookingForEmployee, FireEmployee, Payment from Administration) are
    # unconnected — they print to console via the models' output() methods.

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
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "scripted"
    main(mode)
