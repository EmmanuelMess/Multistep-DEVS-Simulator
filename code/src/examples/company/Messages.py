from dataclasses import dataclass


@dataclass
class Product:
    id: str
    product_type: str


@dataclass
class DemandProduct:
    id: str
    product_type: str


@dataclass
class OfferProduct:
    id: str
    product_type: str


@dataclass
class Capital:
    id: str
    amount: float


@dataclass
class Payment:
    id: str
    amount: float


@dataclass
class Employee:
    id: str


@dataclass
class EmployeeOffering:
    id: str
    employee: Employee


@dataclass
class EmployeeResignation:
    id: str
    employee: Employee


@dataclass
class LookingForEmployee:
    id: str


@dataclass
class FireEmployee:
    id: str
    employee: Employee


@dataclass
class AssignEmployee:
    id: str
    employee: Employee


@dataclass
class HaltProduction:
    id: str


@dataclass
class RequestEmployee:
    id: str
    sender: str


@dataclass
class StartImprovements:
    id: str
    product_type: str


@dataclass
class Improvement:
    id: str
    product_type: str
    efficiency_gain: float


@dataclass
class ImprovementsCost:
    id: str
    cost: float
