import random
from collections import defaultdict
from enum import Enum
from typing import List, Tuple, Any, Dict, Callable

from src.devs.AtomicGraph import AtomicGraph
from src.devs.IdGenerator import generateId
from src.devs.Port import Port
from src.devs.Simulator import Simulator
from src.devs.Types import Time
from src.examples.company.Administration import Administration
from src.examples.company.ExternalSource import ExternalSource
from src.examples.company.Manufacturing import Manufacturing
from src.examples.company.Messages import (
    Capital, Payment, DemandProduct, Product, Employee,
    EmployeeOffering, EmployeeResignation, OfferProduct,
)
from src.examples.company.RAndD import RAndD

Mode = Enum('Mode', [('SCRIPTED', 1), ('RANDOM', 2)])


class CompanyGraph:
    # Simulation configuration
    PRODUCT_CONFIG: Dict[str, Dict[str, Any]] = {
        "steel": {"role": "primary", "cost": 3.0},
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

    @staticmethod
    def generate_graph(mode: Mode) -> Tuple[AtomicGraph, Simulator]:
        graph = AtomicGraph()

        if mode == Mode.SCRIPTED:
            events = CompanyGraph._generate_scripted_events
        elif mode == Mode.RANDOM:
            events = CompanyGraph._generate_random_events
        else:
            raise ValueError(f"Unknown mode: {mode}")

        CompanyGraph._build_graph(graph, events)

        simulator = Simulator(graph)

        return graph, simulator

    @staticmethod
    def _generate_scripted_events(external_source: ExternalSource) -> Dict[Time, List[Tuple[Port, Any]]]:
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
        events[1.0].append((external_source.CAPITAL_OUT, Capital(generateId("capital"), 200.0)))

        # t=2,4: Employees arrive early
        for t in [2.0, 4.0]:
            employee = Employee(generateId("employee"))
            events[t].append(
                (external_source.EMPLOYEE_OFFERING_OUT, EmployeeOffering(generateId("employee_offer"), employee)))
            employees.append(employee)

        # t=3: First demand for a widget
        events[3.0].append((external_source.DEMAND_PRODUCT_OUT, DemandProduct(generateId("demand"), "widget")))

        # t=5,6: Steel deliveries (2 needed per widget)
        events[5.0].append((external_source.PRODUCT_OUT,
                            Product(generateId("product"), "steel")))
        events[6.0].append((external_source.PRODUCT_OUT,
                            Product(generateId("product"), "steel")))

        # t=7: Payment from customer for the first widget (honor system)
        events[7.0].append((external_source.PAYMENT_OUT,
                            Payment(generateId("payment"), 12.0)))

        # t=8: Third employee arrives
        emp3 = Employee(generateId("employee"))
        events[8.0].append((external_source.EMPLOYEE_OFFERING_OUT,
                            EmployeeOffering(generateId("employee_offer"), emp3)))
        employees.append(emp3)

        # t=9,10: More demand + steel for a second widget
        events[9.0].append((external_source.DEMAND_PRODUCT_OUT,
                            DemandProduct(generateId("demand"), "widget")))
        events[10.0].append((external_source.PRODUCT_OUT,
                             Product(generateId("product"), "steel")))
        events[10.5].append((external_source.PRODUCT_OUT,
                             Product(generateId("product"), "steel")))

        # t=11: Payment for second widget
        events[11.0].append((external_source.PAYMENT_OUT,
                             Payment(generateId("payment"), 12.0)))

        # t=12: Outside offers steel to the company (Administration pays)
        events[12.0].append((external_source.OFFER_PRODUCT_OUT,
                             OfferProduct(generateId("offer"), "steel", 3.0)))

        # t=14: Third demand + more steel
        events[14.0].append((external_source.DEMAND_PRODUCT_OUT,
                             DemandProduct(generateId("demand"), "widget")))
        events[14.5].append((external_source.PRODUCT_OUT,
                             Product(generateId("product"), "steel")))
        events[15.0].append((external_source.PRODUCT_OUT,
                             Product(generateId("product"), "steel")))
        events[16.0].append((external_source.PAYMENT_OUT,
                             Payment(generateId("payment"), 12.0)))

        # t=20: Fourth employee arrives
        emp4 = Employee(generateId("employee"))
        events[20.0].append((external_source.EMPLOYEE_OFFERING_OUT,
                             EmployeeOffering(generateId("employee_offer"), emp4)))
        employees.append(emp4)

        # t=25: Employee resignation (second employee resigns)
        events[25.0].append((external_source.EMPLOYEE_RESIGNATION_OUT,
                             EmployeeResignation(generateId("resign"), employees[1])))

        # --- GAP: no demand from t=16 to t=55 ---
        # Administration should halt production after IDLE_THRESHOLD_REVIEWS

        # t=55: Demand returns -> triggers undo halt
        events[55.0].append((external_source.DEMAND_PRODUCT_OUT,
                             DemandProduct(generateId("demand"), "widget")))
        events[56.0].append((external_source.PRODUCT_OUT,
                             Product(generateId("product"), "steel")))
        events[56.5].append((external_source.PRODUCT_OUT,
                             Product(generateId("product"), "steel")))
        events[58.0].append((external_source.PAYMENT_OUT,
                             Payment(generateId("payment"), 12.0)))

        # t=60: Fifth employee (to trigger FireEmployee if over max)
        employee = Employee(generateId("employee"))
        events[60.0].append((external_source.EMPLOYEE_OFFERING_OUT,
                             EmployeeOffering(generateId("employee_offer"), employee)))
        employees.append(employee)

        return dict(events)

    @staticmethod
    def _generate_random_events(external_source: ExternalSource,
                                seed: int = 42, max_time: float = 100.0,
                                ) -> Dict[Time, List[Tuple[Port, Any]]]:
        """Generate events from exponential inter-arrival distributions.

        Exercises all message types via random scheduling.
        """
        rng = random.Random(seed)
        e: Dict[Time, List[Tuple[Port, Any]]] = defaultdict(list)

        # Capital — one-shot at start
        e[0.5].append((external_source.CAPITAL_OUT,
                       Capital(generateId("capital"), 200.0)))

        # Customer demand (exponential, mean 5.0)
        t = 0.0
        for _ in range(40):
            t += rng.expovariate(1.0 / 5.0)
            if t > max_time:
                break
            e[round(t, 4)].append((external_source.DEMAND_PRODUCT_OUT,
                                   DemandProduct(generateId("demand"), "widget")))

        # Raw material deliveries (exponential, mean 3.0)
        t = 1.0
        for _ in range(60):
            t += rng.expovariate(1.0 / 3.0)
            if t > max_time:
                break
            e[round(t, 4)].append((external_source.PRODUCT_OUT,
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
            e[round(t, 4)].append((external_source.EMPLOYEE_OFFERING_OUT,
                                   EmployeeOffering(generateId("employee_offer"), employee)))

        # Payments (follow demand with some delay)
        t = 3.0
        for _ in range(30):
            t += rng.expovariate(1.0 / 6.0)
            if t > max_time:
                break
            pay = round(rng.uniform(8.0, 15.0), 2)
            e[round(t, 4)].append((external_source.PAYMENT_OUT,
                                   Payment(generateId("payment"), pay)))

        # Outside offers products to the company (exponential, mean 15.0)
        t = 5.0
        for _ in range(10):
            t += rng.expovariate(1.0 / 15.0)
            if t > max_time:
                break
            cost = round(rng.uniform(2.0, 5.0), 2)
            e[round(t, 4)].append((external_source.OFFER_PRODUCT_OUT,
                                   OfferProduct(generateId("offer"), "steel", cost)))

        # Employee resignations (sparse, exponential, mean 30.0)
        t = 20.0
        for _ in range(3):
            t += rng.expovariate(1.0 / 30.0)
            if t > max_time or not employees:
                break
            employee = rng.choice(employees)
            employees.remove(employee)
            e[round(t, 4)].append((external_source.EMPLOYEE_RESIGNATION_OUT,
                                   EmployeeResignation(generateId("resign"), employee)))

        return dict(e)

    @staticmethod
    def _build_graph(graph: AtomicGraph, generate_events: Callable[[ExternalSource], Dict[Time, List[Tuple[Port, Any]]]]) \
            -> None:
        """
        Wiring
        """
        # --- Create models ---
        manufacturing = Manufacturing(
            bill_of_materials=CompanyGraph.BILL_OF_MATERIALS,
            product_costs=CompanyGraph.PRODUCT_COSTS,
        )
        rnd = RAndD(
            improvement_duration=10.0,
            efficiency_gain=0.1,
            improvement_cost=20.0,
        )
        admin = Administration(
            mfg_id=manufacturing.id,
            rnd_id=rnd.id,
            producible_products=CompanyGraph.PRODUCIBLE_PRODUCTS,
            max_employees=10,
        )
        source = ExternalSource(generate_events)

        graph.add_all([manufacturing, rnd, admin, source])

        # --- Internal connections (per DEVS diagram) ---

        # Administration -> Manufacturing:
        #   { ForceHaltProduction, UndoHaltProduction,
        #     AssignEmployee, UnassignEmployee }
        graph.connect(admin.ASSIGN_EMPLOYEE_MFG_OUT, manufacturing.ASSIGN_EMPLOYEE_IN)
        graph.connect(admin.UNASSIGN_EMPLOYEE_MFG_OUT, manufacturing.UNASSIGN_EMPLOYEE_IN)
        graph.connect(admin.FORCE_HALT_PRODUCTION_OUT, manufacturing.FORCE_HALT_PRODUCTION_IN)
        graph.connect(admin.UNDO_HALT_PRODUCTION_OUT, manufacturing.UNDO_HALT_PRODUCTION_IN)

        # Manufacturing -> Administration:
        #   { RequestEmployee, DemandProduct(Product(i)) }
        graph.connect(manufacturing.REQUEST_EMPLOYEE_OUT, admin.REQUEST_EMPLOYEE_IN)
        graph.connect(manufacturing.DEMAND_PRODUCT_OUT, admin.DEMAND_PRODUCT_IN)

        # Administration -> R&D:
        #   { AssignEmployee, UnassignEmployee, StartImprovements }
        graph.connect(admin.ASSIGN_EMPLOYEE_RD_OUT, rnd.ASSIGN_EMPLOYEE_IN)
        graph.connect(admin.UNASSIGN_EMPLOYEE_RD_OUT, rnd.UNASSIGN_EMPLOYEE_IN)
        graph.connect(admin.START_IMPROVEMENTS_OUT, rnd.START_IMPROVEMENTS_IN)

        # R&D -> Administration:
        #   { RequestEmployee, ImprovementsCost, InformImprovementFinished }
        graph.connect(rnd.REQUEST_EMPLOYEE_OUT, admin.REQUEST_EMPLOYEE_IN)
        graph.connect(rnd.IMPROVEMENTS_COST_OUT, admin.IMPROVEMENTS_COST_IN)
        graph.connect(rnd.INFORM_IMPROVEMENT_FINISHED_OUT, admin.INFORM_IMPROVEMENT_FINISHED_IN)

        # R&D -> Manufacturing: { Improvement }
        graph.connect(rnd.IMPROVEMENT_OUT, manufacturing.IMPROVEMENT_IN)

        # --- External connections (ExternalSource -> Company inputs) ---

        # Capital, Payment -> Administration
        graph.connect(source.CAPITAL_OUT, admin.CAPITAL_IN)
        graph.connect(source.PAYMENT_OUT, admin.PAYMENT_IN)

        # EmployeeOffering, EmployeeResignation, OfferProduct -> Administration
        graph.connect(source.EMPLOYEE_OFFERING_OUT, admin.EMPLOYEE_OFFERING_IN)
        graph.connect(source.EMPLOYEE_RESIGNATION_OUT, admin.EMPLOYEE_RESIGNATION_IN)
        graph.connect(source.OFFER_PRODUCT_OUT, admin.OFFER_PRODUCT_IN)

        # DemandProduct -> Manufacturing
        graph.connect(source.DEMAND_PRODUCT_OUT, manufacturing.DEMAND_PRODUCT_IN)

        # Product (raw materials) -> Manufacturing
        graph.connect(source.PRODUCT_OUT, manufacturing.PRODUCT_IN)

        # Company outputs (Product, OfferProduct from Manufacturing;
        # LookingForEmployee, FireEmployee, DemandProduct, Payment
        # from Administration) are unconnected — they print to console
        # via the models' output() methods.